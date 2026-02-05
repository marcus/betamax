---
sidebar_position: 5
title: Themes
---

# Themes

Betamax includes 31 built-in color themes for styling GIF and PNG decorations (window bar, padding, margin). Themes set colors for the decorative areas around your terminal content -- the terminal content itself uses your termshot color palette.

## Using Themes

**CLI flag:**
```bash
betamax myapp -f demo.keys --theme dracula
```

**@set directive in a keys file:**
```
@set:theme:catppuccin-mocha
```

**Config file (`.betamaxrc` or global config):**
```bash
theme=nord
```

### Overriding Theme Colors

Explicit color settings take precedence over theme values. Set a theme for base colors, then override individual properties:

```
@set:theme:dracula
@set:bar_color:ff0000
@set:margin:20
```

This applies Dracula's padding and margin colors but uses a custom red bar color.

## Dark Themes

### Catppuccin

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `catppuccin-mocha` | `#1e1e2e` | `#1e1e2e` | `#11111b` |
| `catppuccin-macchiato` | `#24273a` | `#24273a` | `#181926` |
| `catppuccin-frappe` | `#303446` | `#303446` | `#232634` |

### Gruvbox

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `gruvbox-dark` | `#282828` | `#282828` | `#1d2021` |

### Tokyo Night

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `tokyo-night` | `#1a1b26` | `#1a1b26` | `#13141c` |
| `tokyo-night-storm` | `#24283b` | `#24283b` | `#1a1e2e` |

### Solarized

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `solarized-dark` | `#002b36` | `#002b36` | `#001e26` |

### Rose Pine

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `rose-pine` | `#191724` | `#191724` | `#12101a` |
| `rose-pine-moon` | `#232136` | `#232136` | `#1a1829` |

### Everforest

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `everforest-dark` | `#2d353b` | `#2d353b` | `#232a2e` |

### GitHub

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `github-dark` | `#0d1117` | `#0d1117` | `#010409` |
| `github-dark-dimmed` | `#22272e` | `#22272e` | `#1c2128` |

### Ayu

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `ayu-dark` | `#0a0e14` | `#0a0e14` | `#050709` |
| `ayu-mirage` | `#1f2430` | `#1f2430` | `#171b24` |

### Material

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `material` | `#263238` | `#263238` | `#1a2327` |
| `material-darker` | `#212121` | `#212121` | `#171717` |

### Other Dark Themes

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `dracula` | `#282a36` | `#282a36` | `#1e1f29` |
| `nord` | `#2e3440` | `#2e3440` | `#242933` |
| `one-dark` | `#282c34` | `#282c34` | `#1e2127` |
| `monokai` | `#272822` | `#272822` | `#1e1f1c` |
| `kanagawa` | `#1f1f28` | `#1f1f28` | `#16161d` |
| `night-owl` | `#011627` | `#011627` | `#00101c` |
| `palenight` | `#292d3e` | `#292d3e` | `#1e212e` |
| `synthwave-84` | `#262335` | `#262335` | `#1a1726` |
| `cyberpunk` | `#000b1e` | `#000b1e` | `#000714` |

## Light Themes

| Theme | Bar | Padding | Margin |
|-------|-----|---------|--------|
| `catppuccin-latte` | `#eff1f5` | `#eff1f5` | `#dce0e8` |
| `gruvbox-light` | `#fbf1c7` | `#fbf1c7` | `#f2e5bc` |
| `solarized-light` | `#fdf6e3` | `#fdf6e3` | `#eee8d5` |
| `github-light` | `#ffffff` | `#ffffff` | `#f6f8fa` |
| `rose-pine-dawn` | `#faf4ed` | `#faf4ed` | `#f2e9e1` |
| `everforest-light` | `#fdf6e3` | `#fdf6e3` | `#f3ead3` |

## Theme Properties

Each theme sets three decoration colors:

| Property | Description |
|----------|-------------|
| **Bar** (`bar_color`) | Window bar background color |
| **Padding** (`padding_color`) | Inner padding area around terminal content |
| **Margin** (`margin_color`) | Outer margin area (slightly darker/lighter than padding for depth) |

Theme names are case-insensitive. Underscores and hyphens are interchangeable (`catppuccin_mocha` and `catppuccin-mocha` both work).

## See Also

- [Styling Options](/docs/guides/styling-options) - Window bars, shadows, padding, and more
- [Configuration](/docs/guides/configuration) - Config file locations and precedence
- [CLI Reference](/docs/cli-reference) - `--theme` flag and all options
