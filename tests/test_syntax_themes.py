import pytest
from pygments.style import Style
from termux_dev_setup.utils import syntax_themes

# =================== Test THEME_MAP and get_syntax_theme lookups ===================

def test_get_theme_by_name():
    """Test that all predefined themes can be retrieved by name."""
    for name in syntax_themes.THEME_MAP:
        style_class, bg_color = syntax_themes.get_syntax_theme(name)
        assert issubclass(style_class, Style)
        assert isinstance(bg_color, str)
        assert bg_color.startswith("#")
        assert style_class.background_color == bg_color

def test_get_theme_case_insensitive():
    """Test that theme lookup is case-insensitive."""
    style_class_lower, _ = syntax_themes.get_syntax_theme("cyberpunk")
    style_class_upper, _ = syntax_themes.get_syntax_theme("CYBERPUNK")
    assert style_class_lower == style_class_upper

def test_get_theme_fallback():
    """Test that an unknown theme name falls back to the default."""
    default_class, default_bg = syntax_themes.THEME_MAP["one_dark"]
    style_class, bg_color = syntax_themes.get_syntax_theme("this_theme_does_not_exist")
    assert style_class == default_class
    assert bg_color == default_bg

def test_get_theme_empty_name():
    """Test that an empty theme name also falls back to the default."""
    default_class, default_bg = syntax_themes.THEME_MAP["one_dark"]
    style_class, bg_color = syntax_themes.get_syntax_theme("")
    assert style_class == default_class
    assert bg_color == default_bg

# =================== Test random theme generation ===================

def test_get_random_theme_ephemeral():
    """Test that 'random' produces different themes each time."""
    style1, bg1 = syntax_themes.get_syntax_theme("random")
    style2, bg2 = syntax_themes.get_syntax_theme("random")
    assert style1 != style2
    assert bg1 != bg2

def test_get_random_theme_deterministic_by_seed():
    """Test that 'random:<seed>' is deterministic."""
    style1, bg1 = syntax_themes.get_syntax_theme("random:123")
    style2, bg2 = syntax_themes.get_syntax_theme("random:123")
    style3, bg3 = syntax_themes.get_syntax_theme("r:123") # Test alias
    assert style1 == style2
    assert bg1 == bg2
    assert style1 == style3

def test_get_random_theme_different_seeds():
    """Test that different seeds produce different themes."""
    style1, bg1 = syntax_themes.get_syntax_theme("random:123")
    style2, bg2 = syntax_themes.get_syntax_theme("random:456")
    assert style1 != style2
    assert bg1 != bg2

def test_get_random_theme_string_seed_hashing():
    """Test that string seeds are hashed to an integer."""
    style1, bg1 = syntax_themes.get_syntax_theme("random:my_seed_string")
    style2, bg2 = syntax_themes.get_syntax_theme("random:my_seed_string")
    style3, bg3 = syntax_themes.get_syntax_theme("random:another_string")
    assert style1 == style2
    assert bg1 == bg2
    assert style1 != style3


# =================== Test color utility functions ===================

@pytest.mark.parametrize("h, s, l, expected_rgb", [
    (0, 1, 0.5, (255, 0, 0)),      # Red
    (120, 1, 0.5, (0, 255, 0)),    # Green
    (240, 1, 0.5, (0, 0, 255)),    # Blue
    (0, 0, 1, (255, 255, 255)),    # White
    (0, 0, 0, (0, 0, 0)),          # Black
    (60, 0.5, 0.25, (96, 96, 32)), # Dark Yellow
])
def test_hsl_to_rgb(h, s, lightness, expected_rgb):
    assert syntax_themes.hsl_to_rgb(h, s, lightness) == expected_rgb

def test_rgb_to_hex():
    assert syntax_themes.rgb_to_hex((255, 10, 128)) == "#ff0a80"

def test_relative_luminance():
    assert syntax_themes.relative_luminance("#000000") == pytest.approx(0.0)
    assert syntax_themes.relative_luminance("#ffffff") == pytest.approx(1.0)
    assert syntax_themes.relative_luminance("#ff0000") == pytest.approx(0.2126)

def test_contrast_ratio():
    # Maximum contrast (black vs white)
    assert syntax_themes.contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0)
    # No contrast (white vs white)
    assert syntax_themes.contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0)
    # WCAG AA minimum for normal text
    assert syntax_themes.contrast_ratio("#757575", "#ffffff") > 4.5
