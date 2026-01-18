#!/bin/bash
# betamax test harness

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$SCRIPT_DIR/output"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

PASSED=0
FAILED=0

pass() {
  echo -e "${GREEN}✓${NC} $1"
  ((PASSED++)) || true
}

fail() {
  echo -e "${RED}✗${NC} $1"
  ((FAILED++)) || true
}

warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

cleanup() {
  rm -rf "$OUTPUT_DIR"
}

# Run before tests
setup() {
  echo "Setting up..."
  cleanup
  mkdir -p "$OUTPUT_DIR"
}

# Test capture formats
test_capture_formats() {
  echo ""
  echo "=== Testing capture formats ==="

  # Run betamax with the capture test keys file
  "$PROJECT_DIR/betamax" bash -f "$SCRIPT_DIR/capture_formats.keys" 2>&1

  echo ""
  echo "Verifying outputs..."

  # Check txt format
  if [[ -f "$OUTPUT_DIR/test_txt.txt" ]]; then
    if grep -q "Betamax Capture Test" "$OUTPUT_DIR/test_txt.txt"; then
      pass "txt format: file created with content"
    else
      fail "txt format: file created but missing expected content"
    fi
  else
    fail "txt format: file not created"
  fi

  # Check html format
  if [[ -f "$OUTPUT_DIR/test_html.html" ]]; then
    if grep -q "<html" "$OUTPUT_DIR/test_html.html" && grep -q "Betamax" "$OUTPUT_DIR/test_html.html"; then
      pass "html format: file created with HTML structure"
    else
      fail "html format: file created but invalid structure"
    fi
  else
    if command -v aha &>/dev/null; then
      fail "html format: file not created (aha available)"
    else
      warn "html format: skipped (aha not installed)"
    fi
  fi

  # Check png format
  if [[ -f "$OUTPUT_DIR/test_png.png" ]]; then
    # Check PNG magic bytes
    if file "$OUTPUT_DIR/test_png.png" | grep -q "PNG"; then
      pass "png format: valid PNG file created"
    else
      fail "png format: file created but not valid PNG"
    fi
  else
    if command -v termshot &>/dev/null; then
      fail "png format: file not created (termshot available)"
    else
      warn "png format: skipped (termshot not installed)"
    fi
  fi

  # Check 'all' format (should create txt, html, png)
  local all_count=0
  [[ -f "$OUTPUT_DIR/test_all.txt" ]] && { ((all_count++)) || true; }
  [[ -f "$OUTPUT_DIR/test_all.html" ]] && { ((all_count++)) || true; }
  [[ -f "$OUTPUT_DIR/test_all.png" ]] && { ((all_count++)) || true; }

  if [[ $all_count -eq 3 ]]; then
    pass "all format: created txt, html, and png"
  elif [[ $all_count -gt 0 ]]; then
    pass "all format: created $all_count/3 formats (based on available tools)"
  else
    fail "all format: no files created"
  fi
}

# Test basic functionality
test_basic() {
  echo ""
  echo "=== Testing basic functionality ==="

  # Test help
  if "$PROJECT_DIR/betamax" --help | grep -q "Terminal session recorder"; then
    pass "help: displays usage"
  else
    fail "help: missing usage text"
  fi

  # Test missing command error
  if "$PROJECT_DIR/betamax" 2>&1 | grep -q "No command specified"; then
    pass "validation: errors on missing command"
  else
    fail "validation: should error on missing command"
  fi

  # Test simple command with capture (run bash, then echo)
  local simple_out
  simple_out=$("$PROJECT_DIR/betamax" -c bash -- "echo testoutput" Enter 2>&1)
  if echo "$simple_out" | grep -q "testoutput"; then
    pass "execution: captures command output"
  else
    fail "execution: failed to capture output"
  fi
}

# Test inline delay
test_inline_delay() {
  echo ""
  echo "=== Testing inline delay ==="

  local start end elapsed
  start=$(date +%s)
  "$PROJECT_DIR/betamax" bash -- "echo fast@50" Enter "echo slow@1000" Enter 2>&1
  end=$(date +%s)
  elapsed=$((end - start))

  if [[ $elapsed -ge 1 ]]; then
    pass "inline delay: respected custom timing"
  else
    fail "inline delay: timing not respected (elapsed: ${elapsed}s)"
  fi
}

# Test @sleep directive
test_sleep_directive() {
  echo ""
  echo "=== Testing @sleep directive ==="

  local start end elapsed
  start=$(date +%s)
  "$PROJECT_DIR/betamax" bash -- "@sleep:1000" Enter 2>&1
  end=$(date +%s)
  elapsed=$((end - start))

  if [[ $elapsed -ge 1 ]]; then
    pass "@sleep: waited 1000ms"
  else
    fail "@sleep: did not wait (elapsed: ${elapsed}s)"
  fi
}

# Test sidecar plugin navigation
test_sidecar() {
  echo ""
  echo "=== Testing sidecar plugin capture ==="

  if ! command -v sidecar &>/dev/null; then
    warn "sidecar: not installed, skipping"
    return 0
  fi

  local sidecar_out="$OUTPUT_DIR/sidecar"
  mkdir -p "$sidecar_out"

  # Run sidecar with plugin capture keys
  "$PROJECT_DIR/betamax" sidecar -w Sidecar -f "$SCRIPT_DIR/sidecar-plugins.keys" 2>&1

  echo ""
  echo "Verifying sidecar outputs..."

  local plugins=("td" "git" "files" "conversations" "worktrees")
  local captured=0

  for plugin in "${plugins[@]}"; do
    if [[ -f "$sidecar_out/plugin-${plugin}.png" ]]; then
      if file "$sidecar_out/plugin-${plugin}.png" | grep -q "PNG"; then
        pass "sidecar: captured $plugin plugin"
        ((captured++)) || true
      else
        fail "sidecar: $plugin capture not valid PNG"
      fi
    else
      fail "sidecar: $plugin plugin not captured"
    fi
  done

  if [[ $captured -eq 5 ]]; then
    pass "sidecar: all 5 plugins captured successfully"
  fi
}

# Test GIF recording with vim
test_gif_recording() {
  echo ""
  echo "=== Testing GIF recording ==="

  if ! command -v vim &>/dev/null; then
    warn "gif: vim not installed, skipping"
    return 0
  fi

  if ! command -v termshot &>/dev/null; then
    warn "gif: termshot not installed, skipping"
    return 0
  fi

  if ! command -v ffmpeg &>/dev/null; then
    warn "gif: ffmpeg not installed, skipping"
    return 0
  fi

  # Run vim with GIF recording (--clean skips config, shortmess+=I skips intro)
  "$PROJECT_DIR/betamax" 'vim --clean -c "set shortmess+=I"' -o "$OUTPUT_DIR" -f "$SCRIPT_DIR/vim_gif.keys" 2>&1

  echo ""
  echo "Verifying GIF output..."

  if [[ -f "$OUTPUT_DIR/vim_test.gif" ]]; then
    # Check if it's a valid GIF
    if file "$OUTPUT_DIR/vim_test.gif" | grep -q "GIF"; then
      local size=$(stat -f%z "$OUTPUT_DIR/vim_test.gif" 2>/dev/null || stat -c%s "$OUTPUT_DIR/vim_test.gif" 2>/dev/null)
      if [[ "$size" -gt 1000 ]]; then
        pass "gif: valid GIF created (${size} bytes)"
      else
        fail "gif: GIF too small (${size} bytes)"
      fi
    else
      fail "gif: file not valid GIF format"
    fi
  else
    fail "gif: vim_test.gif not created"
  fi
}

# Test gradient wave GIF (animated rainbow logo)
test_gradient_wave() {
  echo ""
  echo "=== Testing gradient wave GIF ==="

  if ! command -v termshot &>/dev/null; then
    warn "gradient: termshot not installed, skipping"
    return 0
  fi

  if ! command -v ffmpeg &>/dev/null; then
    warn "gradient: ffmpeg not installed, skipping"
    return 0
  fi

  # Run bash with gradient wave keys file
  "$PROJECT_DIR/betamax" bash -o "$OUTPUT_DIR" -f "$SCRIPT_DIR/gradient_wave.keys" 2>&1

  echo ""
  echo "Verifying gradient wave GIF..."

  if [[ -f "$OUTPUT_DIR/gradient_wave.gif" ]]; then
    if file "$OUTPUT_DIR/gradient_wave.gif" | grep -q "GIF"; then
      local size=$(stat -f%z "$OUTPUT_DIR/gradient_wave.gif" 2>/dev/null || stat -c%s "$OUTPUT_DIR/gradient_wave.gif" 2>/dev/null)
      if [[ "$size" -gt 5000 ]]; then
        pass "gradient: valid GIF created (${size} bytes)"
      else
        fail "gradient: GIF too small (${size} bytes)"
      fi
    else
      fail "gradient: file not valid GIF format"
    fi
  else
    fail "gradient: gradient_wave.gif not created"
  fi
}

# Summary
summary() {
  echo ""
  echo "================================"
  echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
  echo "================================"

  if [[ $FAILED -gt 0 ]]; then
    exit 1
  fi
}

# Run validation tests
run_validation_tests() {
  echo ""
  echo "=== Running validation tests ==="
  if "$SCRIPT_DIR/validation_tests.sh"; then
    pass "validation tests: all passed"
  else
    fail "validation tests: some failed"
  fi
}

# Main
main() {
  setup
  run_validation_tests
  test_basic
  test_capture_formats
  test_inline_delay
  test_sleep_directive
  test_gif_recording
  test_gradient_wave
  test_sidecar
  summary
}

main "$@"
