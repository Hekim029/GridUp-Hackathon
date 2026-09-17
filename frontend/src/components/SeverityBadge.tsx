import type { Severity } from "../types";

const labels: Record<Severity, string> = {
  normal: "Normal",
  watch: "İzle",
  warning: "Uyarı",
  critical: "Kritik",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`severity severity-${severity}`}>{labels[severity]}</span>;
}

