"""
themes.py - Terminal color themes for betamax GIF decorations

Provides popular color themes for styling GIF decorations (window bar, margins,
padding). Terminal content colors depend on termshot's built-in palette and
cannot be themed.

Usage:
    from themes import THEMES, get_theme, apply_theme_to_options

    theme = get_theme('dracula')
    options = apply_theme_to_options(theme, existing_options)
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Theme:
    """Theme definition for GIF decorations."""
    name: str
    bar_color: str      # Window bar background
    padding_color: str  # Inner padding color (around terminal)
    margin_color: str   # Outer margin color


# Popular terminal themes with their signature colors
# Colors chosen to complement each theme's aesthetic
THEMES: Dict[str, Theme] = {
    # Dark themes
    'dracula': Theme(
        name='Dracula',
        bar_color='#282a36',
        padding_color='#282a36',
        margin_color='#1e1f29',
    ),
    'catppuccin-mocha': Theme(
        name='Catppuccin Mocha',
        bar_color='#1e1e2e',
        padding_color='#1e1e2e',
        margin_color='#11111b',
    ),
    'catppuccin-macchiato': Theme(
        name='Catppuccin Macchiato',
        bar_color='#24273a',
        padding_color='#24273a',
        margin_color='#181926',
    ),
    'catppuccin-frappe': Theme(
        name='Catppuccin Frappe',
        bar_color='#303446',
        padding_color='#303446',
        margin_color='#232634',
    ),
    'catppuccin-latte': Theme(
        name='Catppuccin Latte',
        bar_color='#eff1f5',
        padding_color='#eff1f5',
        margin_color='#dce0e8',
    ),
    'gruvbox-dark': Theme(
        name='Gruvbox Dark',
        bar_color='#282828',
        padding_color='#282828',
        margin_color='#1d2021',
    ),
    'gruvbox-light': Theme(
        name='Gruvbox Light',
        bar_color='#fbf1c7',
        padding_color='#fbf1c7',
        margin_color='#f2e5bc',
    ),
    'nord': Theme(
        name='Nord',
        bar_color='#2e3440',
        padding_color='#2e3440',
        margin_color='#242933',
    ),
    'tokyo-night': Theme(
        name='Tokyo Night',
        bar_color='#1a1b26',
        padding_color='#1a1b26',
        margin_color='#13141c',
    ),
    'tokyo-night-storm': Theme(
        name='Tokyo Night Storm',
        bar_color='#24283b',
        padding_color='#24283b',
        margin_color='#1a1e2e',
    ),
    'one-dark': Theme(
        name='One Dark',
        bar_color='#282c34',
        padding_color='#282c34',
        margin_color='#1e2127',
    ),
    'monokai': Theme(
        name='Monokai',
        bar_color='#272822',
        padding_color='#272822',
        margin_color='#1e1f1c',
    ),
    'solarized-dark': Theme(
        name='Solarized Dark',
        bar_color='#002b36',
        padding_color='#002b36',
        margin_color='#001e26',
    ),
    'solarized-light': Theme(
        name='Solarized Light',
        bar_color='#fdf6e3',
        padding_color='#fdf6e3',
        margin_color='#eee8d5',
    ),
    'github-dark': Theme(
        name='GitHub Dark',
        bar_color='#0d1117',
        padding_color='#0d1117',
        margin_color='#010409',
    ),
    'github-dark-dimmed': Theme(
        name='GitHub Dark Dimmed',
        bar_color='#22272e',
        padding_color='#22272e',
        margin_color='#1c2128',
    ),
    'github-light': Theme(
        name='GitHub Light',
        bar_color='#ffffff',
        padding_color='#ffffff',
        margin_color='#f6f8fa',
    ),
    'ayu-dark': Theme(
        name='Ayu Dark',
        bar_color='#0a0e14',
        padding_color='#0a0e14',
        margin_color='#050709',
    ),
    'ayu-mirage': Theme(
        name='Ayu Mirage',
        bar_color='#1f2430',
        padding_color='#1f2430',
        margin_color='#171b24',
    ),
    'rose-pine': Theme(
        name='Rose Pine',
        bar_color='#191724',
        padding_color='#191724',
        margin_color='#12101a',
    ),
    'rose-pine-moon': Theme(
        name='Rose Pine Moon',
        bar_color='#232136',
        padding_color='#232136',
        margin_color='#1a1829',
    ),
    'rose-pine-dawn': Theme(
        name='Rose Pine Dawn',
        bar_color='#faf4ed',
        padding_color='#faf4ed',
        margin_color='#f2e9e1',
    ),
    'everforest-dark': Theme(
        name='Everforest Dark',
        bar_color='#2d353b',
        padding_color='#2d353b',
        margin_color='#232a2e',
    ),
    'everforest-light': Theme(
        name='Everforest Light',
        bar_color='#fdf6e3',
        padding_color='#fdf6e3',
        margin_color='#f3ead3',
    ),
    'kanagawa': Theme(
        name='Kanagawa',
        bar_color='#1f1f28',
        padding_color='#1f1f28',
        margin_color='#16161d',
    ),
    'material': Theme(
        name='Material',
        bar_color='#263238',
        padding_color='#263238',
        margin_color='#1a2327',
    ),
    'material-darker': Theme(
        name='Material Darker',
        bar_color='#212121',
        padding_color='#212121',
        margin_color='#171717',
    ),
    'night-owl': Theme(
        name='Night Owl',
        bar_color='#011627',
        padding_color='#011627',
        margin_color='#00101c',
    ),
    'palenight': Theme(
        name='Palenight',
        bar_color='#292d3e',
        padding_color='#292d3e',
        margin_color='#1e212e',
    ),
    'synthwave-84': Theme(
        name='Synthwave 84',
        bar_color='#262335',
        padding_color='#262335',
        margin_color='#1a1726',
    ),
    'cyberpunk': Theme(
        name='Cyberpunk',
        bar_color='#000b1e',
        padding_color='#000b1e',
        margin_color='#000714',
    ),
}


def get_theme(name: str) -> Optional[Theme]:
    """
    Get a theme by name.

    Args:
        name: Theme name (case-insensitive, underscores accepted)

    Returns:
        Theme object or None if not found
    """
    # Normalize name: lowercase, convert underscores to hyphens
    normalized = name.lower().replace('_', '-')
    return THEMES.get(normalized)


def list_themes() -> list:
    """Return list of available theme names."""
    return sorted(THEMES.keys())


def apply_theme_to_options(theme: Theme, options_dict: dict) -> dict:
    """
    Apply theme colors to options, unless explicitly overridden.

    Only applies theme colors if the corresponding option is not already set.
    This allows users to set @set:theme:dracula and then override specific colors.

    Args:
        theme: Theme to apply
        options_dict: Existing options dict (modified in place)

    Returns:
        Modified options dict
    """
    # Only apply if not explicitly set
    if not options_dict.get('bar_color'):
        options_dict['bar_color'] = theme.bar_color
    if not options_dict.get('padding_color'):
        options_dict['padding_color'] = theme.padding_color
    if not options_dict.get('margin_color'):
        options_dict['margin_color'] = theme.margin_color

    return options_dict


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Usage: themes.py <command> [args]')
        print('Commands:')
        print('  list              List all available themes')
        print('  get <name>        Get theme details')
        print('  validate <name>   Check if theme exists')
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'list':
        for name in list_themes():
            theme = THEMES[name]
            print(f'{name}: {theme.name}')

    elif cmd == 'get':
        if len(sys.argv) < 3:
            print('Error: theme name required', file=sys.stderr)
            sys.exit(1)
        name = sys.argv[2]
        theme = get_theme(name)
        if theme:
            print(f'name={theme.name}')
            print(f'bar_color={theme.bar_color}')
            print(f'padding_color={theme.padding_color}')
            print(f'margin_color={theme.margin_color}')
        else:
            print(f'Error: theme not found: {name}', file=sys.stderr)
            sys.exit(1)

    elif cmd == 'validate':
        if len(sys.argv) < 3:
            print('Error: theme name required', file=sys.stderr)
            sys.exit(1)
        name = sys.argv[2]
        if get_theme(name):
            print('valid')
        else:
            print('invalid')
            sys.exit(1)

    else:
        print(f'Unknown command: {cmd}', file=sys.stderr)
        sys.exit(1)
