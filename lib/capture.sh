#!/bin/bash
# betamax/lib/capture.sh - Screen capture functions

capture_to_file() {
  local name="$1"
  local format="$2"  # txt, html, png, or "all"

  mkdir -p "$OUTPUT_DIR"
  local txt_file="$OUTPUT_DIR/$name.txt"

  # Always capture ANSI text first (needed for all formats)
  tmux_cmd capture-pane -t "$SESSION" -e -p > "$txt_file"

  case "$format" in
    txt)
      echo "Saved: $txt_file"
      ;;
    html)
      if command -v aha &>/dev/null; then
        cat "$txt_file" | aha --black > "$OUTPUT_DIR/$name.html"
        echo "Saved: $OUTPUT_DIR/$name.html"
      else
        echo "Warning: aha not installed, skipping HTML"
      fi
      rm -f "$txt_file"
      ;;
    png)
      if command -v termshot &>/dev/null; then
        local cols
        cols=$(tmux_cmd display-message -t "$SESSION" -p '#{pane_width}')
        termshot --raw-read "$txt_file" --columns "$cols" --filename "$OUTPUT_DIR/$name.png" 2>/dev/null
        echo "Saved: $OUTPUT_DIR/$name.png"
      else
        echo "Warning: termshot not installed, skipping PNG"
      fi
      rm -f "$txt_file"
      ;;
    all)
      echo "Saved: $txt_file"
      if command -v aha &>/dev/null; then
        cat "$txt_file" | aha --black > "$OUTPUT_DIR/$name.html"
        echo "Saved: $OUTPUT_DIR/$name.html"
      fi
      if command -v termshot &>/dev/null; then
        local cols
        cols=$(tmux_cmd display-message -t "$SESSION" -p '#{pane_width}')
        termshot --raw-read "$txt_file" --columns "$cols" --filename "$OUTPUT_DIR/$name.png" 2>/dev/null
        echo "Saved: $OUTPUT_DIR/$name.png"
      fi
      ;;
  esac
}

capture_to_stdout() {
  local count="$1"
  echo "=== Capture #$count ==="
  tmux_cmd capture-pane -t "$SESSION" -p 2>/dev/null || echo "(session ended)"
  echo "========================"
}

capture_final() {
  sleep "$DELAY_SEC"
  echo "=== Final pane state ==="
  tmux_cmd capture-pane -t "$SESSION" -p 2>/dev/null || echo "(session ended)"
  echo "========================"
}
