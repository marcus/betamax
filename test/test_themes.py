"""
Unit tests for themes.py
"""

import sys
import os

# Add lib/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib', 'python'))

import pytest
from themes import (
    Theme,
    THEMES,
    get_theme,
    list_themes,
    apply_theme_to_options,
)


class TestTheme:
    """Tests for Theme dataclass."""

    def test_theme_creation(self):
        """Theme can be created with required fields."""
        theme = Theme(
            name='Test',
            bar_color='#1e1e1e',
            padding_color='#2e2e2e',
            margin_color='#3e3e3e',
        )
        assert theme.name == 'Test'
        assert theme.bar_color == '#1e1e1e'
        assert theme.padding_color == '#2e2e2e'
        assert theme.margin_color == '#3e3e3e'


class TestThemesRegistry:
    """Tests for THEMES dictionary."""

    def test_has_popular_themes(self):
        """THEMES contains popular terminal themes."""
        popular = ['dracula', 'nord', 'gruvbox-dark', 'one-dark', 'github-dark']
        for name in popular:
            assert name in THEMES, f'Missing popular theme: {name}'

    def test_all_themes_have_valid_colors(self):
        """All themes have valid hex color strings."""
        for name, theme in THEMES.items():
            # Check each color is valid hex
            for color_name in ['bar_color', 'padding_color', 'margin_color']:
                color = getattr(theme, color_name)
                assert color.startswith('#'), f'{name}.{color_name} missing # prefix'
                assert len(color) == 7, f'{name}.{color_name} wrong length: {color}'
                # Check hex digits
                try:
                    int(color[1:], 16)
                except ValueError:
                    pytest.fail(f'{name}.{color_name} invalid hex: {color}')

    def test_theme_count(self):
        """Should have at least 10 themes as per spec."""
        assert len(THEMES) >= 10, f'Only {len(THEMES)} themes, expected at least 10'

    def test_catppuccin_variants(self):
        """All Catppuccin variants are available."""
        variants = ['catppuccin-mocha', 'catppuccin-macchiato', 'catppuccin-frappe', 'catppuccin-latte']
        for name in variants:
            assert name in THEMES, f'Missing Catppuccin variant: {name}'


class TestGetTheme:
    """Tests for get_theme function."""

    def test_get_existing_theme(self):
        """get_theme returns theme for valid name."""
        theme = get_theme('dracula')
        assert theme is not None
        assert theme.name == 'Dracula'

    def test_get_nonexistent_theme(self):
        """get_theme returns None for invalid name."""
        assert get_theme('nonexistent-theme') is None
        assert get_theme('') is None

    def test_case_insensitive(self):
        """get_theme is case-insensitive."""
        assert get_theme('DRACULA') is not None
        assert get_theme('Dracula') is not None
        assert get_theme('DrAcUlA') is not None

    def test_underscore_to_hyphen(self):
        """get_theme accepts underscores as hyphens."""
        assert get_theme('gruvbox_dark') is not None
        assert get_theme('tokyo_night') is not None
        assert get_theme('catppuccin_mocha') is not None


class TestListThemes:
    """Tests for list_themes function."""

    def test_returns_sorted_list(self):
        """list_themes returns sorted list of theme names."""
        themes = list_themes()
        assert isinstance(themes, list)
        assert themes == sorted(themes)

    def test_all_themes_included(self):
        """list_themes includes all registered themes."""
        themes = list_themes()
        for name in THEMES.keys():
            assert name in themes


class TestApplyThemeToOptions:
    """Tests for apply_theme_to_options function."""

    def test_applies_all_colors(self):
        """apply_theme_to_options sets all theme colors."""
        theme = get_theme('dracula')
        options = {}
        result = apply_theme_to_options(theme, options)

        assert result['bar_color'] == theme.bar_color
        assert result['padding_color'] == theme.padding_color
        assert result['margin_color'] == theme.margin_color

    def test_preserves_explicit_overrides(self):
        """apply_theme_to_options preserves explicitly set colors."""
        theme = get_theme('dracula')
        options = {
            'bar_color': '#ff0000',  # Explicit override
            'padding_color': '',      # Empty = not set
        }
        result = apply_theme_to_options(theme, options)

        # bar_color preserved (was set)
        assert result['bar_color'] == '#ff0000'
        # padding_color from theme (was empty)
        assert result['padding_color'] == theme.padding_color
        # margin_color from theme (was missing)
        assert result['margin_color'] == theme.margin_color

    def test_modifies_in_place(self):
        """apply_theme_to_options modifies the dict in place."""
        theme = get_theme('nord')
        options = {}
        result = apply_theme_to_options(theme, options)
        assert result is options


class TestThemeColors:
    """Tests for specific theme color values."""

    def test_dracula_colors(self):
        """Dracula theme has correct signature colors."""
        theme = get_theme('dracula')
        assert theme.bar_color == '#282a36'

    def test_nord_colors(self):
        """Nord theme has correct signature colors."""
        theme = get_theme('nord')
        assert theme.bar_color == '#2e3440'

    def test_light_themes_have_light_colors(self):
        """Light themes have light background colors."""
        light_themes = ['catppuccin-latte', 'gruvbox-light', 'solarized-light', 'github-light', 'rose-pine-dawn']
        for name in light_themes:
            theme = get_theme(name)
            if theme:
                # Check bar_color is light (high RGB values)
                r = int(theme.bar_color[1:3], 16)
                g = int(theme.bar_color[3:5], 16)
                b = int(theme.bar_color[5:7], 16)
                avg = (r + g + b) / 3
                assert avg > 200, f'{name} bar_color too dark: {theme.bar_color} (avg={avg})'

    def test_dark_themes_have_dark_colors(self):
        """Dark themes have dark background colors."""
        dark_themes = ['dracula', 'nord', 'gruvbox-dark', 'one-dark', 'github-dark']
        for name in dark_themes:
            theme = get_theme(name)
            if theme:
                # Check bar_color is dark (low RGB values)
                r = int(theme.bar_color[1:3], 16)
                g = int(theme.bar_color[3:5], 16)
                b = int(theme.bar_color[5:7], 16)
                avg = (r + g + b) / 3
                assert avg < 80, f'{name} bar_color too light: {theme.bar_color} (avg={avg})'


class TestCLI:
    """Tests for command-line interface."""

    def test_list_command(self):
        """CLI list command works."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), '..', 'lib', 'python', 'themes.py')
        result = subprocess.run([sys.executable, script, 'list'], capture_output=True, text=True)
        assert result.returncode == 0
        assert 'dracula' in result.stdout

    def test_get_command(self):
        """CLI get command works."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), '..', 'lib', 'python', 'themes.py')
        result = subprocess.run([sys.executable, script, 'get', 'dracula'], capture_output=True, text=True)
        assert result.returncode == 0
        assert 'bar_color=#282a36' in result.stdout

    def test_validate_command_valid(self):
        """CLI validate command returns 0 for valid theme."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), '..', 'lib', 'python', 'themes.py')
        result = subprocess.run([sys.executable, script, 'validate', 'nord'], capture_output=True, text=True)
        assert result.returncode == 0
        assert 'valid' in result.stdout

    def test_validate_command_invalid(self):
        """CLI validate command returns 1 for invalid theme."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), '..', 'lib', 'python', 'themes.py')
        result = subprocess.run([sys.executable, script, 'validate', 'nonexistent'], capture_output=True, text=True)
        assert result.returncode == 1
