# RASA C Library Makefile
# Compiles asn1c-generated code into a static library

CC = cc
CFLAGS = -Wall -Wextra -O2 -I./generated
AR = ar
ARFLAGS = rcs

GENERATED_DIR = generated
BUILD_DIR = build
LIB_NAME = librasa.a

# Generated source files
SOURCES = $(wildcard $(GENERATED_DIR)/*.c)
OBJECTS = $(patsubst $(GENERATED_DIR)/%.c,$(BUILD_DIR)/%.o,$(SOURCES))

.PHONY: all clean test

all: $(BUILD_DIR) $(LIB_NAME)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/%.o: $(GENERATED_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

$(LIB_NAME): $(OBJECTS)
	$(AR) $(ARFLAGS) $@ $(OBJECTS)

test: all
	@echo "Library compiled successfully: $(LIB_NAME)"
	@echo "Objects: $(wordcount $(OBJECTS)) files"

clean:
	rm -rf $(BUILD_DIR) $(LIB_NAME)

install: all
	@echo "Installing RASA library..."
	@echo "Include: $(GENERATED_DIR)/*.h"
	@echo "Library: $(LIB_NAME)"

help:
	@echo "RASA C Library Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all     - Build the static library"
	@echo "  test    - Verify compilation"
	@echo "  clean   - Remove build artifacts"
	@echo "  install - Show installation paths"
