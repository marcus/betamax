"""
decorations.py - Generate visual decorations for GIF recordings

Generates decoration images (window bars, corner masks) for FFmpeg compositing.
Uses Pillow if available, falls back to ImageMagick commands.
"""

import subprocess
import os
from typing import Optional, Tuple, Dict

# Color palettes for different bar styles
BAR_STYLES = {
    'colorful': {
        'dots': ['#ff5f56', '#ffbd2e', '#27c93f'],  # red, yellow, green
        'default_bg': '#1e1e1e',
    },
    'colorful_right': {
        'dots': ['#ff5f56', '#ffbd2e', '#27c93f'],
        'default_bg': '#1e1e1e',
        'align': 'right',
    },
    'rings': {
        'dots': ['#ff5f56', '#ffbd2e', '#27c93f'],
        'default_bg': '#1e1e1e',
        'hollow': True,
    },
}

# Default dimensions
DEFAULT_BAR_HEIGHT = 30
DEFAULT_DOT_RADIUS = 6
DEFAULT_DOT_SPACING = 20
DEFAULT_DOT_MARGIN = 20


def _validate_hex_color(color: str) -> str:
    """
    Validate and normalize hex color format.

    Args:
        color: Hex color string (with or without # prefix)

    Returns:
        Normalized color with # prefix

    Raises:
        ValueError: If color format is invalid
    """
    if not color:
        raise ValueError('Color cannot be empty')

    # Normalize: add # prefix if missing
    if not color.startswith('#'):
        color = '#' + color

    # Validate hex format
    hex_part = color[1:]
    if len(hex_part) not in (3, 6):
        raise ValueError(f'Invalid hex color length: {color} (expected 3 or 6 hex digits)')

    try:
        int(hex_part, 16)
    except ValueError:
        raise ValueError(f'Invalid hex color format: {color} (contains non-hex characters)')

    return color


def _validate_dimensions(value: int, name: str, min_val: int = 1, max_val: int = 10000) -> int:
    """Validate numeric dimensions."""
    if not isinstance(value, int):
        raise TypeError(f'{name} must be int, got {type(value).__name__}')
    if value < min_val or value > max_val:
        raise ValueError(f'{name} must be between {min_val} and {max_val}, got {value}')
    return value


def _validate_output_path(path: str, recording_dir: str = None) -> str:
    """
    Validate output path to prevent path traversal.

    Args:
        path: Output path to validate
        recording_dir: If provided, path must be within this directory

    Returns:
        Normalized absolute path

    Raises:
        ValueError: If path contains traversal or is outside allowed directory
    """
    if not path:
        raise ValueError('Output path cannot be empty')

    # Normalize path
    norm_path = os.path.normpath(os.path.abspath(path))

    # Check for null bytes (common injection vector)
    if '\x00' in path:
        raise ValueError('Output path contains null bytes')

    # If recording_dir specified, ensure path is within it
    if recording_dir:
        norm_dir = os.path.normpath(os.path.abspath(recording_dir))
        if not norm_path.startswith(norm_dir + os.sep) and norm_path != norm_dir:
            raise ValueError(f'Output path must be within {recording_dir}')

    return norm_path


def _validate_border_radius(radius: int, width: int, height: int) -> int:
    """
    Validate border radius against dimensions.

    Args:
        radius: Border radius in pixels
        width: Image width
        height: Image height

    Returns:
        Validated radius

    Raises:
        ValueError: If radius is invalid
    """
    if not isinstance(radius, int):
        raise TypeError(f'radius must be int, got {type(radius).__name__}')
    if radius < 0:
        raise ValueError(f'radius cannot be negative: {radius}')

    max_radius = min(width, height) // 2
    if radius > max_radius:
        raise ValueError(f'radius {radius} exceeds max {max_radius} for {width}x{height}')

    return radius


def _check_pillow() -> bool:
    """Check if Pillow is available."""
    try:
        from PIL import Image, ImageDraw
        return True
    except ImportError:
        return False


def _check_imagemagick() -> bool:
    """Check if ImageMagick is available."""
    try:
        result = subprocess.run(['convert', '-version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def generate_window_bar_pillow(
    width: int,
    output_path: str,
    style: str = 'colorful',
    bg_color: str = None,
    bar_height: int = DEFAULT_BAR_HEIGHT,
) -> bool:
    """Generate window bar PNG using Pillow."""
    from PIL import Image, ImageDraw

    # Validate inputs
    _validate_dimensions(width, 'width')
    _validate_dimensions(bar_height, 'bar_height', max_val=500)

    style_config = BAR_STYLES.get(style, BAR_STYLES['colorful'])
    bg = bg_color or style_config['default_bg']
    bg = _validate_hex_color(bg)  # Validate color to prevent issues
    dots = style_config['dots']
    align_right = style_config.get('align') == 'right'
    hollow = style_config.get('hollow', False)

    img = Image.new('RGBA', (width, bar_height), bg)
    draw = ImageDraw.Draw(img)

    dot_y = bar_height // 2
    dot_radius = DEFAULT_DOT_RADIUS

    for i, color in enumerate(dots):
        if align_right:
            x = width - DEFAULT_DOT_MARGIN - (len(dots) - 1 - i) * DEFAULT_DOT_SPACING
        else:
            x = DEFAULT_DOT_MARGIN + i * DEFAULT_DOT_SPACING

        bbox = [x - dot_radius, dot_y - dot_radius,
                x + dot_radius, dot_y + dot_radius]

        if hollow:
            draw.ellipse(bbox, outline=color, width=2)
        else:
            draw.ellipse(bbox, fill=color)

    img.save(output_path, 'PNG')
    return True


def generate_window_bar_imagemagick(
    width: int,
    output_path: str,
    style: str = 'colorful',
    bg_color: str = None,
    bar_height: int = DEFAULT_BAR_HEIGHT,
) -> bool:
    """Generate window bar PNG using ImageMagick."""
    # Validate inputs - CRITICAL for security (prevents command injection)
    _validate_dimensions(width, 'width')
    _validate_dimensions(bar_height, 'bar_height', max_val=500)

    style_config = BAR_STYLES.get(style, BAR_STYLES['colorful'])
    bg = bg_color or style_config['default_bg']
    bg = _validate_hex_color(bg)  # CRITICAL: validate before shell interpolation
    dots = style_config['dots']
    align_right = style_config.get('align') == 'right'
    hollow = style_config.get('hollow', False)

    dot_y = bar_height // 2
    dot_radius = DEFAULT_DOT_RADIUS

    cmd = ['convert', '-size', f'{width}x{bar_height}', f'xc:{bg}']

    for i, color in enumerate(dots):
        if align_right:
            x = width - DEFAULT_DOT_MARGIN - (len(dots) - 1 - i) * DEFAULT_DOT_SPACING
        else:
            x = DEFAULT_DOT_MARGIN + i * DEFAULT_DOT_SPACING

        if hollow:
            cmd.extend([
                '-fill', 'none',
                '-stroke', color,
                '-strokewidth', '2',
                '-draw', f'circle {x},{dot_y} {x + dot_radius},{dot_y}'
            ])
        else:
            cmd.extend([
                '-fill', color,
                '-draw', f'circle {x},{dot_y} {x + dot_radius},{dot_y}'
            ])

    cmd.append(output_path)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            import sys
            print(f'ImageMagick error: {result.stderr}', file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        import sys
        print('ImageMagick not found. Install with: brew install imagemagick', file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        import sys
        print('ImageMagick timed out generating window bar', file=sys.stderr)
        return False


def generate_window_bar(
    width: int,
    output_path: str,
    style: str = 'colorful',
    bg_color: str = None,
    bar_height: int = DEFAULT_BAR_HEIGHT,
) -> bool:
    """
    Generate window bar PNG for GIF decoration.

    Args:
        width: Width of the bar (matches video width)
        output_path: Where to save the PNG
        style: Bar style ('colorful', 'colorful_right', 'rings')
        bg_color: Background color (hex, e.g. '#1e1e1e')
        bar_height: Height of the bar in pixels

    Returns:
        True on success, False on failure
    """
    if _check_pillow():
        return generate_window_bar_pillow(width, output_path, style, bg_color, bar_height)
    elif _check_imagemagick():
        return generate_window_bar_imagemagick(width, output_path, style, bg_color, bar_height)
    else:
        return False


def generate_corner_mask_pillow(
    width: int,
    height: int,
    output_path: str,
    radius: int,
) -> bool:
    """Generate rounded corner alpha mask using Pillow."""
    from PIL import Image, ImageDraw

    # Validate inputs
    _validate_dimensions(width, 'width')
    _validate_dimensions(height, 'height')
    _validate_border_radius(radius, width, height)

    # Create mask with alpha channel
    mask = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(mask)

    # Draw black (transparent) corners
    # Top-left
    draw.rectangle([0, 0, radius, radius], fill=0)
    draw.pieslice([0, 0, radius * 2, radius * 2], 180, 270, fill=255)

    # Top-right
    draw.rectangle([width - radius, 0, width, radius], fill=0)
    draw.pieslice([width - radius * 2, 0, width, radius * 2], 270, 360, fill=255)

    # Bottom-left
    draw.rectangle([0, height - radius, radius, height], fill=0)
    draw.pieslice([0, height - radius * 2, radius * 2, height], 90, 180, fill=255)

    # Bottom-right
    draw.rectangle([width - radius, height - radius, width, height], fill=0)
    draw.pieslice([width - radius * 2, height - radius * 2, width, height], 0, 90, fill=255)

    mask.save(output_path, 'PNG')
    return True


def generate_corner_mask_imagemagick(
    width: int,
    height: int,
    output_path: str,
    radius: int,
) -> bool:
    """Generate rounded corner alpha mask using ImageMagick."""
    # Validate inputs
    _validate_dimensions(width, 'width')
    _validate_dimensions(height, 'height')
    _validate_border_radius(radius, width, height)

    cmd = [
        'convert', '-size', f'{width}x{height}',
        'xc:white',
        '-fill', 'black',
        # Top-left corner
        '-draw', f'rectangle 0,0 {radius},{radius}',
        '-fill', 'white',
        '-draw', f'circle {radius},{radius} {radius},0',
        # Top-right corner
        '-fill', 'black',
        '-draw', f'rectangle {width - radius},0 {width},{radius}',
        '-fill', 'white',
        '-draw', f'circle {width - radius - 1},{radius} {width - radius - 1},0',
        # Bottom-left corner
        '-fill', 'black',
        '-draw', f'rectangle 0,{height - radius} {radius},{height}',
        '-fill', 'white',
        '-draw', f'circle {radius},{height - radius - 1} {radius},{height - 1}',
        # Bottom-right corner
        '-fill', 'black',
        '-draw', f'rectangle {width - radius},{height - radius} {width},{height}',
        '-fill', 'white',
        '-draw', f'circle {width - radius - 1},{height - radius - 1} {width - 1},{height - radius - 1}',
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            import sys
            print(f'ImageMagick error: {result.stderr}', file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        import sys
        print('ImageMagick not found. Install with: brew install imagemagick', file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        import sys
        print('ImageMagick timed out generating corner mask', file=sys.stderr)
        return False


def generate_corner_mask(
    width: int,
    height: int,
    output_path: str,
    radius: int,
) -> bool:
    """
    Generate rounded corner alpha mask.

    Args:
        width: Width of the mask
        height: Height of the mask
        output_path: Where to save the PNG
        radius: Corner radius in pixels

    Returns:
        True on success, False on failure
    """
    if _check_pillow():
        return generate_corner_mask_pillow(width, height, output_path, radius)
    elif _check_imagemagick():
        return generate_corner_mask_imagemagick(width, height, output_path, radius)
    else:
        return False


def _validate_shadow_params(
    blur_radius: int,
    offset_x: int,
    offset_y: int,
    opacity: float,
    color: str,
) -> Tuple[int, int, int, float, str]:
    """Validate shadow parameters."""
    if not isinstance(blur_radius, int):
        raise TypeError(f'blur_radius must be int, got {type(blur_radius).__name__}')
    if blur_radius < 0 or blur_radius > 100:
        raise ValueError(f'blur_radius must be 0-100, got {blur_radius}')

    if not isinstance(offset_x, int):
        raise TypeError(f'offset_x must be int, got {type(offset_x).__name__}')
    if offset_x < -200 or offset_x > 200:
        raise ValueError(f'offset_x must be -200 to 200, got {offset_x}')

    if not isinstance(offset_y, int):
        raise TypeError(f'offset_y must be int, got {type(offset_y).__name__}')
    if offset_y < -200 or offset_y > 200:
        raise ValueError(f'offset_y must be -200 to 200, got {offset_y}')

    if not isinstance(opacity, (int, float)):
        raise TypeError(f'opacity must be float, got {type(opacity).__name__}')
    if opacity < 0.0 or opacity > 1.0:
        raise ValueError(f'opacity must be 0.0-1.0, got {opacity}')

    color = _validate_hex_color(color)
    return blur_radius, offset_x, offset_y, float(opacity), color


def _calculate_shadow_canvas_size(
    width: int,
    height: int,
    blur_radius: int,
    offset_x: int,
    offset_y: int,
) -> Tuple[int, int, int]:
    """Calculate shadow canvas dimensions and padding."""
    padding = blur_radius * 2 + max(abs(offset_x), abs(offset_y))
    shadow_width = width + padding * 2
    shadow_height = height + padding * 2
    return shadow_width, shadow_height, padding


def generate_shadow_pillow(
    width: int,
    height: int,
    output_path: str,
    blur_radius: int = 15,
    offset_x: int = 0,
    offset_y: int = 8,
    opacity: float = 0.4,
    color: str = '#000000',
    source_mask_path: Optional[str] = None,
) -> bool:
    """
    Generate drop shadow image using Pillow.

    Creates an RGBA image where the alpha channel contains the blurred shadow.

    Args:
        width: Width of content to cast shadow
        height: Height of content to cast shadow
        output_path: Where to save the shadow PNG
        blur_radius: Gaussian blur radius in pixels
        offset_x: Horizontal shadow offset (positive = right)
        offset_y: Vertical shadow offset (positive = down)
        opacity: Shadow opacity 0.0-1.0
        color: Shadow color as hex string
        source_mask_path: Optional path to alpha mask for shadow shape

    Returns:
        True on success, False on failure
    """
    from PIL import Image, ImageDraw, ImageFilter

    # Validate inputs
    _validate_dimensions(width, 'width')
    _validate_dimensions(height, 'height')
    blur_radius, offset_x, offset_y, opacity, color = _validate_shadow_params(
        blur_radius, offset_x, offset_y, opacity, color
    )

    # Calculate canvas size
    shadow_width, shadow_height, padding = _calculate_shadow_canvas_size(
        width, height, blur_radius, offset_x, offset_y
    )

    # Create alpha mask for shadow shape
    alpha = Image.new('L', (shadow_width, shadow_height), 0)

    # Position of content area in shadow canvas (offset applied)
    content_x = padding + offset_x
    content_y = padding + offset_y

    if source_mask_path and os.path.exists(source_mask_path):
        # Use existing corner mask as shadow shape
        mask = Image.open(source_mask_path).convert('L')
        alpha.paste(mask, (content_x, content_y))
    else:
        # Draw solid rectangle
        draw = ImageDraw.Draw(alpha)
        draw.rectangle(
            [content_x, content_y, content_x + width - 1, content_y + height - 1],
            fill=255
        )

    # Apply gaussian blur
    if blur_radius > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(blur_radius))

    # Scale alpha by opacity
    if opacity < 1.0:
        alpha = alpha.point(lambda p: int(p * opacity))

    # Parse shadow color
    hex_part = color[1:]
    if len(hex_part) == 3:
        hex_part = ''.join(c * 2 for c in hex_part)
    r = int(hex_part[0:2], 16)
    g = int(hex_part[2:4], 16)
    b = int(hex_part[4:6], 16)

    # Create final RGBA image
    shadow = Image.new('RGBA', (shadow_width, shadow_height), (r, g, b, 0))
    shadow.putalpha(alpha)

    shadow.save(output_path, 'PNG')
    return True


def generate_shadow_imagemagick(
    width: int,
    height: int,
    output_path: str,
    blur_radius: int = 15,
    offset_x: int = 0,
    offset_y: int = 8,
    opacity: float = 0.4,
    color: str = '#000000',
    source_mask_path: Optional[str] = None,
) -> bool:
    """
    Generate drop shadow image using ImageMagick.

    Args:
        width: Width of content to cast shadow
        height: Height of content to cast shadow
        output_path: Where to save the shadow PNG
        blur_radius: Gaussian blur radius in pixels
        offset_x: Horizontal shadow offset (positive = right)
        offset_y: Vertical shadow offset (positive = down)
        opacity: Shadow opacity 0.0-1.0
        color: Shadow color as hex string
        source_mask_path: Optional path to alpha mask for shadow shape

    Returns:
        True on success, False on failure
    """
    import sys

    # Validate inputs
    _validate_dimensions(width, 'width')
    _validate_dimensions(height, 'height')
    blur_radius, offset_x, offset_y, opacity, color = _validate_shadow_params(
        blur_radius, offset_x, offset_y, opacity, color
    )

    # Calculate canvas size
    shadow_width, shadow_height, padding = _calculate_shadow_canvas_size(
        width, height, blur_radius, offset_x, offset_y
    )

    content_x = padding + offset_x
    content_y = padding + offset_y

    if source_mask_path and os.path.exists(source_mask_path):
        # Use mask as shadow shape
        cmd = [
            'convert',
            '-size', f'{shadow_width}x{shadow_height}', 'xc:transparent',
            source_mask_path,
            '-geometry', f'+{content_x}+{content_y}',
            '-composite',
            '-channel', 'A', '-blur', f'0x{blur_radius}',
            '-channel', 'A', '-evaluate', 'multiply', str(opacity),
            '+channel',
            '-fill', color, '-colorize', '100%',
            output_path
        ]
    else:
        # Draw rectangle shadow
        cmd = [
            'convert',
            '-size', f'{shadow_width}x{shadow_height}', 'xc:transparent',
            '-fill', 'white',
            '-draw', f'rectangle {content_x},{content_y} {content_x + width - 1},{content_y + height - 1}',
            '-channel', 'A', '-blur', f'0x{blur_radius}',
            '-channel', 'A', '-evaluate', 'multiply', str(opacity),
            '+channel',
            '-fill', color, '-colorize', '100%',
            output_path
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f'ImageMagick error: {result.stderr}', file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        print('ImageMagick not found. Install with: brew install imagemagick', file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print('ImageMagick timed out generating shadow', file=sys.stderr)
        return False


def generate_shadow(
    width: int,
    height: int,
    output_path: str,
    blur_radius: int = 15,
    offset_x: int = 0,
    offset_y: int = 8,
    opacity: float = 0.4,
    color: str = '#000000',
    source_mask_path: Optional[str] = None,
) -> bool:
    """
    Generate drop shadow PNG for GIF decoration.

    Uses Pillow if available, falls back to ImageMagick.

    Args:
        width: Width of content to cast shadow
        height: Height of content to cast shadow
        output_path: Where to save the shadow PNG
        blur_radius: Gaussian blur radius in pixels (default 15)
        offset_x: Horizontal offset, positive = right (default 0)
        offset_y: Vertical offset, positive = down (default 8)
        opacity: Shadow opacity 0.0-1.0 (default 0.4)
        color: Shadow color as hex string (default '#000000')
        source_mask_path: Optional path to alpha mask for shadow shape

    Returns:
        True on success, False on failure
    """
    if _check_pillow():
        return generate_shadow_pillow(
            width, height, output_path, blur_radius,
            offset_x, offset_y, opacity, color, source_mask_path
        )
    elif _check_imagemagick():
        return generate_shadow_imagemagick(
            width, height, output_path, blur_radius,
            offset_x, offset_y, opacity, color, source_mask_path
        )
    else:
        return False


def get_available_backend() -> Optional[str]:
    """Return the available image generation backend."""
    if _check_pillow():
        return 'pillow'
    elif _check_imagemagick():
        return 'imagemagick'
    return None


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Usage: decorations.py <command> [args]')
        print('Commands:')
        print('  window_bar <width> <output> [style] [bg_color]')
        print('  corner_mask <width> <height> <output> <radius>')
        print('  shadow <width> <height> <output> [blur] [offset_x] [offset_y] [opacity] [color] [mask_path]')
        print('  check_backend')
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'window_bar':
        width = int(sys.argv[2])
        output = sys.argv[3]
        style = sys.argv[4] if len(sys.argv) > 4 else 'colorful'
        bg = sys.argv[5] if len(sys.argv) > 5 else None
        if generate_window_bar(width, output, style, bg):
            print(f'Generated: {output}')
        else:
            print('Error: Failed to generate window bar', file=sys.stderr)
            sys.exit(1)

    elif cmd == 'corner_mask':
        width = int(sys.argv[2])
        height = int(sys.argv[3])
        output = sys.argv[4]
        radius = int(sys.argv[5])
        if generate_corner_mask(width, height, output, radius):
            print(f'Generated: {output}')
        else:
            print('Error: Failed to generate corner mask', file=sys.stderr)
            sys.exit(1)

    elif cmd == 'shadow':
        width = int(sys.argv[2])
        height = int(sys.argv[3])
        output = sys.argv[4]
        blur = int(sys.argv[5]) if len(sys.argv) > 5 else 15
        offset_x = int(sys.argv[6]) if len(sys.argv) > 6 else 0
        offset_y = int(sys.argv[7]) if len(sys.argv) > 7 else 8
        opacity = float(sys.argv[8]) if len(sys.argv) > 8 else 0.4
        color = sys.argv[9] if len(sys.argv) > 9 else '#000000'
        mask_path = sys.argv[10] if len(sys.argv) > 10 else None
        if generate_shadow(width, height, output, blur, offset_x, offset_y, opacity, color, mask_path):
            print(f'Generated: {output}')
        else:
            print('Error: Failed to generate shadow', file=sys.stderr)
            sys.exit(1)

    elif cmd == 'check_backend':
        backend = get_available_backend()
        if backend:
            print(backend)
        else:
            print('none')
            sys.exit(1)

    else:
        print(f'Unknown command: {cmd}', file=sys.stderr)
        sys.exit(1)
