from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .domain import NotificationRecord, PanelSnapshot, Severity

logger = logging.getLogger("gridup.notifications")


class SQLiteRepository:
    def __init__(self, database_path: str) -> None:
        self.path = Path(database_path)
        self._last_severity: dict[str, Severity] = {}

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA synchronous=NORMAL")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    panel_id TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_telemetry_panel_time
                    ON telemetry(panel_id, captured_at DESC);
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    panel_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _save_sync(self, snapshots: list[PanelSnapshot]) -> None:
        telemetry_rows = [
            (
                snapshot.telemetry.panel_id,
                snapshot.telemetry.timestamp.isoformat(),
                snapshot.assessment.severity.value,
                snapshot.assessment.score,
                snapshot.model_dump_json(),
            )
            for snapshot in snapshots
        ]
        notification_rows = []
        for snapshot in snapshots:
            panel_id = snapshot.telemetry.panel_id
            severity = snapshot.assessment.severity
            previous = self._last_severity.get(panel_id, Severity.NORMAL)
            escalation = severity in {Severity.WARNING, Severity.CRITICAL} and severity != previous
            if escalation:
                message = (
                    f"{severity.value.upper()}: {panel_id} - {snapshot.assessment.summary} "
                    f"Risk={snapshot.assessment.score:.0f}/100"
                )
                created_at = datetime.now(UTC).isoformat()
                notification_rows.extend(
                    (panel_id, channel, severity.value, message, created_at)
                    for channel in ("sms_simulated", "whatsapp_simulated")
                )
                logger.warning("Simulated notification dispatch: %s", message)
            self._last_severity[panel_id] = severity

        with self._connect() as connection:
            connection.executemany(
                """INSERT INTO telemetry(
                    panel_id, captured_at, severity, risk_score, payload_json
                ) VALUES(?,?,?,?,?)""",
                telemetry_rows,
            )
            if notification_rows:
                connection.executemany(
                    """INSERT INTO notifications(
                        panel_id, channel, severity, message, created_at
                    ) VALUES(?,?,?,?,?)""",
                    notification_rows,
                )

    async def save(self, snapshots: list[PanelSnapshot]) -> None:
        await asyncio.to_thread(self._save_sync, snapshots)

    def notifications(self, limit: int = 50) -> list[NotificationRecord]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """SELECT id, panel_id, channel, severity, message, created_at
                FROM notifications ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            NotificationRecord(
                id=row["id"],
                panel_id=row["panel_id"],
                channel=row["channel"],
                severity=Severity(row["severity"]),
                message=row["message"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def history(self, panel_id: str, limit: int = 120) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM telemetry WHERE panel_id=? ORDER BY id DESC LIMIT ?",
                (panel_id, limit),
            ).fetchall()
        return [json.loads(row[0]) for row in reversed(rows)]
