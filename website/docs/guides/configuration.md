---
sidebar_position: 5
title: Configuration
---

# Configuration

Betamax supports configuration at multiple levels: CLI flags, `@set` directives in keys files, project config files, global config, and named presets. Settings are resolved in a strict precedence chain so you always know which value wins.

## Precedence

When the same setting is specified in multiple places, the highest-priority source wins:

```
CLI flags > @set directives > .betamaxrc > global config > preset > defaults
```

Once a value is set by a higher-priority source, lower-priority sources cannot override it.

## Config File Format

All config files use the same `key=value` format. Lines starting with `#` are comments. Blank lines are ignored.

```bash
# Example config
theme=dracula
window-bar=colorful
border-radius=12
margin=20
padding=10
shadow=true
```

### Available Keys

| Key | Description | Example |
|-----|-------------|---------|
| `theme` | Color theme name | `dracula` |
| `preset` | Load a named preset | `polished` |
| `window-bar` | Window bar style | `colorful` |
| `bar-color` | Bar background color | `#1e1e1e` |
| `bar-height` | Bar height in pixels | `30` |
| `border-radius` | Corner radius in pixels | `12` |
| `margin` | Outer margin in pixels | `20` |
| `margin-color` | Margin background color | `#000000` |
| `padding` | Inner padding in pixels | `10` |
| `padding-color` | Padding background color | `#1e1e1e` |
| `shadow` | Enable drop shadow | `true` |
| `shadow-blur` | Shadow blur radius (0-100) | `15` |
| `shadow-offset-x` | Horizontal shadow offset (-200 to 200) | `0` |
| `shadow-offset-y` | Vertical shadow offset (-200 to 200) | `8` |
| `shadow-opacity` | Shadow opacity (0.0-1.0) | `0.4` |
| `shadow-color` | Shadow color | `#000000` |
| `output-dir` | Output directory for captures | `./captures` |

:::note
Config file keys use **hyphens** (e.g. `bar-color`), while `@set` directives in keys files use **underscores** (e.g. `@set:bar_color:1e1e1e`).
:::

## Project Config (`.betamaxrc`)

Place a `.betamaxrc` file in your project to share settings across all keys files in that directory tree.

Betamax searches for `.betamaxrc` starting from the current directory and walking upward. It stops when it finds the file or reaches a `.git` directory (the repository root).

```
my-project/
  .git/
  .betamaxrc          # <-- found here
  docs/
    demos/
      intro.keys      # uses .betamaxrc from project root
```

Example `.betamaxrc`:

```bash
# Project-wide defaults
theme=catppuccin-mocha
window-bar=colorful
border-radius=10
margin=20
padding=8
shadow=true
output-dir=./docs/img
```

## Global Config

A global config applies to all betamax invocations on your machine. It is loaded after `.betamaxrc`, so project settings take priority.

**Location:** `~/.config/betamax/config`

The path respects `XDG_CONFIG_HOME` if set:

```
${XDG_CONFIG_HOME:-$HOME/.config}/betamax/config
```

Example global config:

```bash
# Personal defaults
theme=nord
shadow=true
shadow-blur=20
```

## Presets

Presets are named config files stored in a central location. Use them to switch between different styling profiles without editing project config.

**Location:** `~/.config/betamax/presets/<name>.conf`

Create a preset:

```bash
mkdir -p ~/.config/betamax/presets

cat > ~/.config/betamax/presets/polished.conf << 'EOF'
window-bar=colorful
border-radius=12
margin=30
padding=10
shadow=true
shadow-blur=20
shadow-opacity=0.5
EOF
```

Use a preset via CLI:

```bash
betamax myapp -f demo.keys --preset polished
```

Or in `.betamaxrc`:

```bash
preset=polished
```

Or in a keys file:

```
@set:theme:dracula
# preset is loaded from .betamaxrc or CLI
```

Presets are loaded after `.betamaxrc` and global config, so they fill in any values not already set. If a preset is not found, betamax prints a warning and continues.

## Config Discovery Flow

The full resolution order for a setting like `margin`:

1. **CLI flag** `--margin 30` -- highest priority
2. **@set directive** `@set:margin:30` in the keys file
3. **`.betamaxrc`** `margin=30` in the nearest project config
4. **Global config** `margin=30` in `~/.config/betamax/config`
5. **Preset** `margin=30` in the loaded preset file
6. **Built-in default** `0`

At each level, a value is only applied if it hasn't already been set by a higher-priority source.

## See Also

- [CLI Reference](/docs/cli-reference) - All command-line flags
- [Keys File Format](/docs/keys-file-format) - `@set` directive reference
- [Styling Options](/docs/guides/styling-options) - Visual customization guide
- [Themes](/docs/themes) - Built-in color themes
