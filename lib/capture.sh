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

# Capture a single frame (called after each key when recording)
recording_capture_frame() {
  if [[ "$RECORDING" != true ]] || [[ "$RECORDING_PAUSED" == true ]]; then
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

  # Build options JSON for Python pipeline
  local opts_json='{'
  opts_json+='"gif_delay":'${GIF_FRAME_DELAY_MS:-200}','
  opts_json+='"speed":'${GIF_PLAYBACK_SPEED:-1.0}

  if [[ -n "$GIF_WINDOW_BAR" && "$GIF_WINDOW_BAR" != "none" ]]; then
    opts_json+=',"window_bar":"'$GIF_WINDOW_BAR'"'
  fi
  if [[ -n "$GIF_BAR_COLOR" ]]; then
    opts_json+=',"bar_color":"'$GIF_BAR_COLOR'"'
  fi
  if [[ -n "$GIF_BORDER_RADIUS" && "$GIF_BORDER_RADIUS" -gt 0 ]] 2>/dev/null; then
    opts_json+=',"border_radius":'$GIF_BORDER_RADIUS
  fi
  if [[ -n "$GIF_MARGIN" && "$GIF_MARGIN" -gt 0 ]] 2>/dev/null; then
    opts_json+=',"margin":'$GIF_MARGIN
  fi
  if [[ -n "$GIF_MARGIN_COLOR" ]]; then
    opts_json+=',"margin_color":"'$GIF_MARGIN_COLOR'"'
  fi
  if [[ -n "$GIF_PADDING" && "$GIF_PADDING" -gt 0 ]] 2>/dev/null; then
    opts_json+=',"padding":'$GIF_PADDING
  fi
  if [[ -n "$GIF_PADDING_COLOR" ]]; then
    opts_json+=',"padding_color":"'$GIF_PADDING_COLOR'"'
  fi

  opts_json+='}'

  # Run Python pipeline to build and execute FFmpeg command
  PYTHONPATH="$python_dir:$PYTHONPATH" python3 -c "
import sys
import os
import subprocess
import json

# Add lib/python to path
sys.path.insert(0, '$python_dir')

from ffmpeg_pipeline import DecorationPipeline, DecorationOptions

opts_dict = json.loads('$opts_json')
options = DecorationOptions(
    window_bar_style=opts_dict.get('window_bar'),
    bar_color=opts_dict.get('bar_color', '#1e1e1e'),
    border_radius=opts_dict.get('border_radius', 0),
    margin=opts_dict.get('margin', 0),
    margin_color=opts_dict.get('margin_color', '#000000'),
    padding=opts_dict.get('padding', 0),
    padding_color=opts_dict.get('padding_color', '#1e1e1e'),
    speed=opts_dict.get('speed', 1.0),
    frame_delay_ms=opts_dict.get('gif_delay', 200),
)

# Get frame dimensions from first frame
first_frame = '$RECORDING_DIR/frame_00000.png'
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
    recording_dir='$RECORDING_DIR',
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
cmd = ['ffmpeg', '-y', '-framerate', '1', '-i', '$RECORDING_DIR/frame_%05d.png']
cmd.extend(input_args)
cmd.extend(['-filter_complex', full_filter, '-map', f'[{output_stream}]', '-r', str(effective_rate), '$OUTPUT_DIR/$output_file'])

# Execute
result = subprocess.run(cmd, capture_output=True)
if result.returncode != 0:
    print(f'FFmpeg error: {result.stderr.decode()}', file=sys.stderr)
    sys.exit(1)
"

  if [[ -f "$OUTPUT_DIR/$output_file" ]]; then
    echo "Saved: $OUTPUT_DIR/$output_file"
  else
    echo "Error: Failed to create GIF"
  fi
}
