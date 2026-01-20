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
  RECORDING_PAUSED=false
  RECORDING_HIDDEN=false
  RECORDING_FRAME=0
  RECORDING_COLS=$(tmux_cmd display-message -t "$SESSION" -p '#{pane_width}')
  echo "Recording started"
}

recording_pause() {
  if [[ "$RECORDING" != true ]]; then
    echo "Warning: Not currently recording"
    return
  fi
  if [[ "$RECORDING_PAUSED" == true ]]; then
    echo "Warning: Recording already paused"
    return
  fi
  RECORDING_PAUSED=true
  echo "Recording paused"
}

recording_resume() {
  if [[ "$RECORDING" != true ]]; then
    echo "Warning: Not currently recording"
    return
  fi
  if [[ "$RECORDING_PAUSED" != true ]]; then
    echo "Warning: Recording not paused"
    return
  fi
  RECORDING_PAUSED=false
  recording_capture_frame  # Capture resume state
  echo "Recording resumed"
}

# Hide recording - keys execute but frames not captured
# Unlike pause, @show doesn't auto-capture a frame
recording_hide() {
  if [[ "$RECORDING" != true ]]; then
    echo "Warning: Not currently recording"
    return
  fi
  if [[ "$RECORDING_HIDDEN" == true ]]; then
    echo "Warning: Recording already hidden"
    return
  fi
  RECORDING_HIDDEN=true
  echo "Recording hidden"
}

# Show recording - resume capturing frames
# Unlike resume, doesn't auto-capture a frame
recording_show() {
  if [[ "$RECORDING" != true ]]; then
    echo "Warning: Not currently recording"
    return
  fi
  if [[ "$RECORDING_HIDDEN" != true ]]; then
    echo "Warning: Recording not hidden"
    return
  fi
  RECORDING_HIDDEN=false
  echo "Recording shown"
}

# Capture a single frame (called after each key when recording)
recording_capture_frame() {
  if [[ "$RECORDING" != true ]] || [[ "$RECORDING_PAUSED" == true ]] || [[ "$RECORDING_HIDDEN" == true ]]; then
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

# Apply loop offset by duplicating initial frames at end
# This creates seamless looping by duplicating the first N frames
apply_loop_offset() {
  local frame_count="$1"

  if [[ -z "$GIF_LOOP_OFFSET" ]] || [[ "$GIF_LOOP_OFFSET" -eq 0 ]]; then
    return 0
  fi

  local delay_ms="${GIF_FRAME_DELAY_MS:-200}"
  local offset_frames=$((GIF_LOOP_OFFSET / delay_ms))

  # Cap at available frames
  if [[ "$offset_frames" -gt "$frame_count" ]]; then
    offset_frames=$frame_count
  fi

  if [[ "$offset_frames" -eq 0 ]]; then
    return 0
  fi

  echo "Applying loop offset: duplicating first $offset_frames frames"

  # Copy first N frames to end
  local src dst
  for ((i=0; i<offset_frames; i++)); do
    src=$(printf "$RECORDING_DIR/frame_%05d.png" $i)
    dst=$(printf "$RECORDING_DIR/frame_%05d.png" $((frame_count + i)))
    if [[ -f "$src" ]]; then
      cp "$src" "$dst"
    fi
  done

  # Update frame count
  RECORDING_FRAME=$((frame_count + offset_frames))
  return $offset_frames
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

  # Apply loop offset (duplicates initial frames at end)
  apply_loop_offset "$frame_count"
  frame_count=$RECORDING_FRAME

  # Ensure output directory exists
  mkdir -p "$OUTPUT_DIR"

  # Check if any decorations are enabled
  local has_decorations=false
  [[ -n "$GIF_WINDOW_BAR" && "$GIF_WINDOW_BAR" != "none" ]] && has_decorations=true
  [[ -n "$GIF_BORDER_RADIUS" && "$GIF_BORDER_RADIUS" -gt 0 ]] 2>/dev/null && has_decorations=true
  [[ -n "$GIF_MARGIN" && "$GIF_MARGIN" -gt 0 ]] 2>/dev/null && has_decorations=true
  [[ -n "$GIF_PADDING" && "$GIF_PADDING" -gt 0 ]] 2>/dev/null && has_decorations=true

  if [[ "$has_decorations" == true ]]; then
    # Use Python pipeline for decorations
    recording_stop_with_decorations "$output_file"
  else
    # Use simple FFmpeg for plain GIF
    recording_stop_simple "$output_file"
  fi

  # Cleanup
  rm -rf "$RECORDING_DIR"
  RECORDING=false
  RECORDING_FRAME=0
}

recording_stop_simple() {
  local output_file="$1"

  # Convert GIF frame delay to centiseconds (100cs = 1 second)
  local delay_cs=$(echo "scale=0; $GIF_FRAME_DELAY_MS / 10" | bc)
  [[ "$delay_cs" -lt 2 ]] && delay_cs=2  # Minimum 20ms per frame

  # Calculate effective delay with playback speed
  # Speed > 1 = faster playback (shorter delay), Speed < 1 = slower
  local effective_delay=$(echo "scale=4; $delay_cs / $GIF_PLAYBACK_SPEED" | bc)
  local effective_rate=$(echo "scale=4; 100 / $effective_delay" | bc)

  # Generate GIF with ffmpeg using frame delay and playback speed
  # reserve_transparent=0 prevents transparency which breaks macOS Preview
  ffmpeg -y -framerate 1 -i "$RECORDING_DIR/frame_%05d.png" \
    -vf "settb=1,setpts=N*$effective_delay/100/TB,split[s0][s1];[s0]palettegen=max_colors=256:stats_mode=diff:reserve_transparent=0[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
    -r $effective_rate \
    "$OUTPUT_DIR/$output_file" 2>/dev/null

  if [[ -f "$OUTPUT_DIR/$output_file" ]]; then
    echo "Saved: $OUTPUT_DIR/$output_file"
  else
    echo "Error: Failed to create GIF"
  fi
}

recording_stop_with_decorations() {
  local output_file="$1"

  # Get script directory to find Python modules
  local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local python_dir="$script_dir/python"

  # Build options JSON safely using environment variables
  # Pass values via env vars instead of shell interpolation to prevent injection
  export BETAMAX_GIF_DELAY="${GIF_FRAME_DELAY_MS:-200}"
  export BETAMAX_SPEED="${GIF_PLAYBACK_SPEED:-1.0}"
  export BETAMAX_WINDOW_BAR="${GIF_WINDOW_BAR:-}"
  export BETAMAX_BAR_COLOR="${GIF_BAR_COLOR:-}"
  export BETAMAX_BAR_HEIGHT="${GIF_BAR_HEIGHT:-30}"
  export BETAMAX_BORDER_RADIUS="${GIF_BORDER_RADIUS:-0}"
  export BETAMAX_MARGIN="${GIF_MARGIN:-0}"
  export BETAMAX_MARGIN_COLOR="${GIF_MARGIN_COLOR:-}"
  export BETAMAX_PADDING="${GIF_PADDING:-0}"
  export BETAMAX_PADDING_COLOR="${GIF_PADDING_COLOR:-}"
  export BETAMAX_RECORDING_DIR="$RECORDING_DIR"
  export BETAMAX_OUTPUT_DIR="$OUTPUT_DIR"
  export BETAMAX_OUTPUT_FILE="$output_file"

  # Run Python pipeline to build and execute FFmpeg command
  # All values passed via environment variables for security
  PYTHONPATH="$python_dir:$PYTHONPATH" python3 -c "
import sys
import os
import subprocess

sys.path.insert(0, os.environ.get('PYTHONPATH', '').split(':')[0])

from ffmpeg_pipeline import DecorationPipeline, DecorationOptions

# Read options from environment variables (safe from shell injection)
def get_env_int(name, default):
    val = os.environ.get(name, '')
    return int(val) if val and val.isdigit() else default

def get_env_float(name, default):
    val = os.environ.get(name, '')
    try:
        return float(val) if val else default
    except ValueError:
        return default

window_bar = os.environ.get('BETAMAX_WINDOW_BAR', '')
options = DecorationOptions(
    window_bar_style=window_bar if window_bar and window_bar != 'none' else None,
    bar_color=os.environ.get('BETAMAX_BAR_COLOR', '') or '#1e1e1e',
    bar_height=get_env_int('BETAMAX_BAR_HEIGHT', 30),
    border_radius=get_env_int('BETAMAX_BORDER_RADIUS', 0),
    margin=get_env_int('BETAMAX_MARGIN', 0),
    margin_color=os.environ.get('BETAMAX_MARGIN_COLOR', '') or '#000000',
    padding=get_env_int('BETAMAX_PADDING', 0),
    padding_color=os.environ.get('BETAMAX_PADDING_COLOR', '') or '#1e1e1e',
    speed=get_env_float('BETAMAX_SPEED', 1.0),
    frame_delay_ms=get_env_int('BETAMAX_GIF_DELAY', 200),
)

recording_dir = os.environ['BETAMAX_RECORDING_DIR']
output_dir = os.environ['BETAMAX_OUTPUT_DIR']
output_file = os.environ['BETAMAX_OUTPUT_FILE']

# Get frame dimensions from first frame
first_frame = os.path.join(recording_dir, 'frame_00000.png')
result = subprocess.run(
    ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
     '-show_entries', 'stream=width,height', '-of', 'csv=p=0', first_frame],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f'Error getting frame dimensions: {result.stderr}', file=sys.stderr)
    sys.exit(1)

dims = result.stdout.strip().split(',')
frame_width, frame_height = int(dims[0]), int(dims[1])

# Build pipeline
pipeline = DecorationPipeline(
    frame_width=frame_width,
    frame_height=frame_height,
    options=options,
    recording_dir=recording_dir,
)

# Calculate effective frame delay with speed
delay_cs = max(2, options.frame_delay_ms // 10)
effective_delay = delay_cs / options.speed
effective_rate = 100 / effective_delay

# Add decorations in correct order
pipeline.add_padding()
pipeline.add_window_bar()
pipeline.add_border_radius()
pipeline.add_margin()

# Build filter complex
input_args, filter_complex, output_stream = pipeline.build()

# Prepend frame setup to filter complex
frames_filter = f'[0:v]settb=1,setpts=N*{effective_delay}/100/TB[frames]'
full_filter = f'{frames_filter};{filter_complex}'

# Build complete command
frame_pattern = os.path.join(recording_dir, 'frame_%05d.png')
output_path = os.path.join(output_dir, output_file)
cmd = ['ffmpeg', '-y', '-framerate', '1', '-i', frame_pattern]
cmd.extend(input_args)
cmd.extend(['-filter_complex', full_filter, '-map', f'[{output_stream}]', '-r', str(effective_rate), output_path])

# Execute
result = subprocess.run(cmd, capture_output=True)
if result.returncode != 0:
    print(f'FFmpeg error: {result.stderr.decode()}', file=sys.stderr)
    sys.exit(1)
"

  # Clean up environment variables
  unset BETAMAX_GIF_DELAY BETAMAX_SPEED BETAMAX_WINDOW_BAR BETAMAX_BAR_COLOR
  unset BETAMAX_BORDER_RADIUS BETAMAX_MARGIN BETAMAX_MARGIN_COLOR
  unset BETAMAX_PADDING BETAMAX_PADDING_COLOR BETAMAX_RECORDING_DIR
  unset BETAMAX_OUTPUT_DIR BETAMAX_OUTPUT_FILE

  if [[ -f "$OUTPUT_DIR/$output_file" ]]; then
    echo "Saved: $OUTPUT_DIR/$output_file"
  else
    echo "Error: Failed to create GIF"
  fi
}
