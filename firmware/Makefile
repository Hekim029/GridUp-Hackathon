CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -pedantic -Iinclude
BUILD_DIR := build
TEST_BIN := $(BUILD_DIR)/test_gridup_edge

.PHONY: all test clean

all: test

$(TEST_BIN): src/gridup_edge.c tests/test_gridup_edge.c include/gridup_edge.h
	mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) src/gridup_edge.c tests/test_gridup_edge.c -lm -o $(TEST_BIN)

test: $(TEST_BIN)
	./$(TEST_BIN)

clean:
	$(RM) -r $(BUILD_DIR)
