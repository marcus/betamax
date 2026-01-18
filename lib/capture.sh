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

# GIF Recording Functions

recording_start() {
  if [[ "$RECORDING" == true ]]; then
    echo "Warning: Recording already in progress"
    return
  fi

  if ! command -v termshot &>/dev/null; then
    echo "Error: termshot required for GIF recording"
    return 1
  fi

  if ! command -v ffmpeg &>/dev/null; then
    echo "Error: ffmpeg required for GIF recording"
    return 1
  fi

  RECORDING_DIR=$(mktemp -d)
  RECORDING=true
  RECORDING_FRAME=0
  RECORDING_COLS=$(tmux_cmd display-message -t "$SESSION" -p '#{pane_width}')
  echo "Recording started"
}

# Capture a single frame (called after each key when recording)
recording_capture_frame() {
  if [[ "$RECORDING" != true ]]; then
    return
  fi

  local frame_file=$(printf "$RECORDING_DIR/frame_%05d.png" $RECORDING_FRAME)
  local txt_file="$RECORDING_DIR/temp.txt"

  # Capture pane (may fail if session ended, that's ok)
  if tmux_cmd capture-pane -t "$SESSION" -e -p > "$txt_file" 2>/dev/null; then
    termshot --raw-read "$txt_file" --columns "$RECORDING_COLS" --filename "$frame_file" 2>/dev/null
    ((RECORDING_FRAME++)) || true
  fi
}

recording_stop() {
  local output_file="$1"

  if [[ "$RECORDING" != true ]]; then
    echo "Warning: No recording in progress"
    return
  fi

  # Capture final frame
  recording_capture_frame

  local frame_count=$RECORDING_FRAME

  if [[ "$frame_count" -eq 0 ]]; then
    echo "Error: No frames captured"
    rm -rf "$RECORDING_DIR"
    RECORDING=false
    return 1
  fi

  echo "Captured $frame_count frames"

  # Ensure output directory exists
  mkdir -p "$OUTPUT_DIR"

  # Convert GIF frame delay to centiseconds (100cs = 1 second)
  local delay_cs=$(echo "scale=0; $GIF_FRAME_DELAY_MS / 10" | bc)
  [[ "$delay_cs" -lt 2 ]] && delay_cs=2  # Minimum 20ms per frame

  # Generate GIF with ffmpeg using frame delay
  # reserve_transparent=0 prevents transparency which breaks macOS Preview
  ffmpeg -y -framerate 1 -i "$RECORDING_DIR/frame_%05d.png" \
    -vf "settb=1,setpts=N*$delay_cs/100/TB,split[s0][s1];[s0]palettegen=max_colors=256:stats_mode=diff:reserve_transparent=0[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
    -r 100/$delay_cs \
    "$OUTPUT_DIR/$output_file" 2>/dev/null

  if [[ -f "$OUTPUT_DIR/$output_file" ]]; then
    echo "Saved: $OUTPUT_DIR/$output_file"
  else
    echo "Error: Failed to create GIF"
  fi

  # Cleanup
  rm -rf "$RECORDING_DIR"
  RECORDING=false
  RECORDING_FRAME=0
}
