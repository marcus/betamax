---
sidebar_position: 1
title: Recording GIFs
---

# Recording GIFs

Betamax can record terminal sessions as animated GIFs, giving you precise control over which frames appear in the final animation.

## Overview

GIF recording is useful for:

- Creating documentation demos
- Recording TUI application workflows
- Generating visual regression tests
- Building tutorials that show terminal interactions

Unlike screen recording tools that capture everything, Betamax captures frames only at explicit points you define. This produces smaller, cleaner GIFs that focus on what matters.

## Prerequisites

GIF recording requires two dependencies:

```bash
# macOS
brew install homeport/tap/termshot ffmpeg

# Or install separately
brew install ffmpeg
brew install homeport/tap/termshot
```

Verify installation:

```bash
which termshot ffmpeg
```

You can also use `@require` in your keys file to fail fast if dependencies are missing:

```bash
@require:termshot
@require:ffmpeg
```

## Basic Recording

A GIF recording session has three parts:

1. `@record:start` - Begin capturing frames
2. `@frame` - Capture the current terminal state
3. `@record:stop:NAME.gif` - Compile frames and save

```bash
@record:start

# ... send keys and capture frames ...

@record:stop:demo.gif
```

Frames are only captured at explicit `@frame` directives. Everything between frames is not recorded.

## Frame Control with @frame

The `@frame` directive captures the current terminal state as a frame in your GIF. Place it after each key or action you want visible in the animation.

```bash
@record:start

i           # Enter insert mode (not captured)
@frame      # Capture after 'i'
H           # Type H (not captured yet)
@frame      # Capture showing 'H'
e           # Type e
@frame      # Capture showing 'He'
l           # Type l
@frame      # Capture showing 'Hel'

@record:stop:typing.gif
```

Only the states captured by `@frame` appear in the final GIF. Keys sent without a following `@frame` are not visible in the animation.

## Sleep with Capture

The `@sleep:MS:capture` syntax combines a pause with frame capture. It captures a frame before and after the sleep, creating a visual pause in the animation.

```bash
@record:start

@frame
# Do something
j
@frame

@sleep:500:capture    # Captures frame, waits 500ms, captures another frame

# Continue
k
@frame

@record:stop:demo.gif
```

This is useful for:

- Adding pauses to let viewers read content
- Showing state changes that happen during a wait
- Creating emphasis on particular states

Note: `@sleep:MS` without `:capture` does not capture frames. Use the explicit `:capture` suffix when you want frames recorded during sleeps.

## Setting GIF Delay

The `@set:gif_delay:MS` directive controls how long each frame displays during playback. The default is 200ms.

```bash
@set:gif_delay:100    # Fast playback (100ms per frame)

@record:start
# ... frames ...
@record:stop:fast.gif
```

```bash
@set:gif_delay:500    # Slow playback (500ms per frame)

@record:start
# ... frames ...
@record:stop:slow.gif
```

Lower values create faster, snappier animations. Higher values give viewers more time to see each frame. Choose based on your content:

- Typing demos: 50-100ms
- UI navigation: 150-200ms
- Complex state changes: 300-500ms

## Playback Speed

The `@set:speed:N` directive controls the overall playback speed multiplier. The default is 1.0 (normal speed).

```bash
@set:speed:2.0    # 2x faster playback

@record:start
# ... frames ...
@record:stop:fast.gif
```

```bash
@set:speed:0.5    # Half speed (slow motion)

@record:start
# ... frames ...
@record:stop:slow.gif
```

Valid speed values range from 0.25 (4x slower) to 4.0 (4x faster):

- `@set:speed:0.25` - Quarter speed (slow motion)
- `@set:speed:0.5` - Half speed
- `@set:speed:1.0` - Normal speed (default)
- `@set:speed:2.0` - Double speed
- `@set:speed:4.0` - Maximum speed

Speed works together with `gif_delay`. A GIF with `@set:gif_delay:200` and `@set:speed:2.0` will play at effectively 100ms per frame.

## Loop Animations with @repeat

The `@repeat:N` and `@end` directives create loops for repetitive frame sequences. This is useful for animations that cycle through states.

```bash
@record:start
@frame

@repeat:10
j           # Navigate down
@frame
@end

@record:stop:scroll.gif
```

The block between `@repeat:N` and `@end` executes N times. This example captures 10 frames of downward navigation.

Loops can include sleeps and multiple keys:

```bash
@record:start

@repeat:24
Enter           # Advance animation frame
@sleep:50
@frame
@end

@record:stop:animation.gif
```

## Complete Example

Here's the output of this example:

![Vim typing demo](/img/demos/vim_hello.gif)

This example records a vim session typing a message:

```bash
# vim_demo.keys

@set:cols:80
@set:rows:24
@set:delay:80
@set:gif_delay:150

@require:termshot
@require:ffmpeg

# Wait for vim to load
@sleep:400

# Start recording and enter insert mode
@record:start
i
@frame

# Type message with frame after each character
B
@frame
e
@frame
t
@frame
a
@frame
m
@frame
a
@frame
x
@frame
Space
@frame
:
@frame
)
@frame

# Exit insert mode and pause to show result
Escape
@sleep:300

# Quit vim
:q!
Enter

@record:stop:vim_demo.gif
```

Run with:

```bash
betamax 'vim --clean -c "set shortmess+=I"' -f vim_demo.keys
```

### Animated Loop Example

This example creates a smooth looping animation by cycling through frames:

```bash
# gradient_animation.keys

@set:cols:50
@set:rows:10
@set:delay:20
@set:gif_delay:50

# Wait for app to display first frame
@sleep:500

# Start recording
@record:start
@frame

# Cycle through 24 animation phases
@repeat:23
Enter
@sleep:50
@frame
@end

@record:stop:gradient_wave.gif
```

## Tips for Smooth Recordings

### Plan Your Frames

Decide which states you want visible before writing the keys file. Not every key press needs a frame.

### Use Consistent Timing

Set `@set:delay:MS` low enough that typing feels natural, but give enough time for the terminal to render between keys.

```bash
@set:delay:80     # 80ms between keys works well for most apps
```

### Set Terminal Size

Always specify terminal dimensions for reproducible recordings:

```bash
@set:cols:80
@set:rows:24
```

### Wait for App Startup

Add a sleep before `@record:start` to ensure the application is fully loaded:

```bash
@sleep:500        # Wait for app
@record:start     # Then start recording
```

### Handle Apps That Exit

For applications that quit (like vim with `:q!`), frames captured after exit are gracefully skipped. Place `@record:stop` after your quit commands.

### Keep GIFs Focused

Shorter, focused GIFs are more effective than long recordings. Aim for 5-15 frames that show a specific workflow.

### Test Without Recording First

Debug your keys file without GIF recording first, then add `@record:start`, `@frame`, and `@record:stop` once the interaction works correctly.
