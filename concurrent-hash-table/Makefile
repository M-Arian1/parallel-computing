# Makefile for Multithreaded Index Mapping

TARGET = concurrent_hash_table
SRCDIR = src
BINDIR = bin
OBJDIR = obj

CC = gcc
CFLAGS = -Wall -Wextra -O3 -std=c99 -D_GNU_SOURCE
LDFLAGS = -lpthread

SOURCES = $(SRCDIR)/main.c $(SRCDIR)/hash_table.c
OBJECTS = $(OBJDIR)/main.o $(OBJDIR)/hash_table.o
HEADERS = $(SRCDIR)/hash_table.h

#default
all: $(BINDIR)/$(TARGET)

$(OBJDIR):
	mkdir -p $(OBJDIR)

$(BINDIR):
	mkdir -p $(BINDIR)

$(BINDIR)/$(TARGET): $(OBJECTS) | $(BINDIR)
	$(CC) $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "Build completed: $@"

$(OBJDIR)/%.o: $(SRCDIR)/%.c $(HEADERS) | $(OBJDIR)
	$(CC) $(CFLAGS) -c $< -o $@

#analyze results
analyze: results
	python3 scripts/analyze_results.py

#clean bin file
clean:
	rm -rf $(OBJDIR) $(BINDIR)/$(TARGET)
	@echo "Clean completed"

#clean results
cleanall: clean
	rm -rf results/*.txt
	rm -f index_output.txt
	@echo "All generated files removed"

results:
	mkdir -p results

#run the test
test-all: $(BINDIR)/$(TARGET) results
	@echo "Running all 99 test configurations..."
	@chmod +x scripts/run_all_tests.sh
	@./scripts/run_all_tests.sh
	@$(MAKE) analyze

#copy the binary file
install: $(BINDIR)/$(TARGET)
	cp $(BINDIR)/$(TARGET) .

#help
help:
	@echo "Available targets:"
	@echo "  all        - Build the program"
	@echo "  clean      - Remove build artifacts"
	@echo "  cleanall   - Remove all generated files"
	@echo "  results    - Create results directory"
	@echo "  test-all   - Run all test configurations"
	@echo "  analyze    - Analyze test results and generate plots"
	@echo "  install    - Copy executable to current directory"
	@echo "  help       - Show this help message"

.PHONY: all clean cleanall results test-all install help analyze
