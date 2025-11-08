"""
Style Constants Module - Centralized styling constants for the application.

Provides consistent colors, fonts, spacing, and styles across all UI components.
"""

from typing import Dict


class Colors:
    """Color palette for the application."""
    
    # Primary colors
    PRIMARY = "#3498db"          # Blue - main brand color
    PRIMARY_DARK = "#2980b9"     # Darker blue for hover states
    PRIMARY_LIGHT = "#5dade2"    # Lighter blue for accents
    
    # Secondary colors
    SECONDARY = "#2c3e50"        # Dark blue-grey
    SECONDARY_LIGHT = "#34495e"  # Lighter blue-grey
    
    # Accent colors
    SUCCESS = "#27ae60"          # Green - success states
    SUCCESS_DARK = "#229954"     # Darker green for hover
    SUCCESS_LIGHT = "#2ecc71"    # Lighter green
    
    WARNING = "#f39c12"          # Orange - warning states
    WARNING_DARK = "#e67e22"     # Darker orange
    WARNING_LIGHT = "#f1c40f"    # Yellow-orange
    
    ERROR = "#e74c3c"            # Red - error states
    ERROR_DARK = "#c0392b"       # Darker red
    ERROR_LIGHT = "#ec7063"      # Lighter red
    
    INFO = "#3498db"             # Blue - info states
    INFO_DARK = "#2980b9"        # Darker blue
    INFO_LIGHT = "#5dade2"       # Lighter blue
    
    # Semantic colors (status indicators)
    VERIFIED = "#27ae60"         # Green - verified status
    PENDING = "#f39c12"          # Orange - pending status
    REJECTED = "#e74c3c"         # Red - rejected status
    
    # Neutral colors
    WHITE = "#ffffff"
    BLACK = "#000000"
    
    # Greys
    GREY_LIGHTEST = "#f8f9fa"    # Background
    GREY_LIGHTER = "#ecf0f1"     # Light backgrounds
    GREY_LIGHT = "#bdc3c7"       # Borders, dividers
    GREY = "#95a5a6"             # Disabled text
    GREY_DARK = "#7f8c8d"        # Secondary text
    GREY_DARKER = "#34495e"      # Primary text
    GREY_DARKEST = "#2c3e50"     # Headers
    
    # Background colors
    BG_PRIMARY = "#ffffff"       # Main background
    BG_SECONDARY = "#f8f9fa"     # Secondary background
    BG_HOVER = "#ecf0f1"         # Hover background
    BG_SELECTED = "#e3f2fd"      # Selected items
    
    # Border colors
    BORDER_LIGHT = "#ecf0f1"
    BORDER_MEDIUM = "#bdc3c7"
    BORDER_DARK = "#95a5a6"
    
    # Text colors
    TEXT_PRIMARY = "#2c3e50"     # Main text
    TEXT_SECONDARY = "#7f8c8d"   # Secondary text
    TEXT_DISABLED = "#95a5a6"    # Disabled text
    TEXT_LIGHT = "#ffffff"       # Light text on dark bg
    
    # Widget-specific colors
    CARD_PRODUCTS = "#3498db"         # Products card
    CARD_POS = "#9b59b6"              # Purchase orders card
    CARD_COUPONS = "#e67e22"          # Coupons card
    CARD_VERIFIED = "#27ae60"         # Verified card
    CARD_PENDING = "#f39c12"          # Pending card
    CARD_CENTRES = "#16a085"          # Medical centres card
    CARD_LOCATIONS = "#8e44ad"        # Distribution locations card
    
    # Alert colors
    ALERT_SUCCESS_BG = "#d4edda"
    ALERT_SUCCESS_BORDER = "#c3e6cb"
    ALERT_SUCCESS_TEXT = "#155724"
    
    ALERT_WARNING_BG = "#fff3cd"
    ALERT_WARNING_BORDER = "#ffc107"
    ALERT_WARNING_TEXT = "#856404"
    
    ALERT_ERROR_BG = "#f8d7da"
    ALERT_ERROR_BORDER = "#f5c6cb"
    ALERT_ERROR_TEXT = "#721c24"
    
    ALERT_INFO_BG = "#d1ecf1"
    ALERT_INFO_BORDER = "#bee5eb"
    ALERT_INFO_TEXT = "#0c5460"


class Fonts:
    """Font definitions for the application."""
    
    # Font families
    FAMILY_PRIMARY = "Segoe UI, Arial, sans-serif"
    FAMILY_MONOSPACE = "Consolas, Monaco, monospace"
    
    # Font sizes (in pixels)
    SIZE_HUGE = 32
    SIZE_XLARGE = 24
    SIZE_LARGE = 18
    SIZE_MEDIUM = 14
    SIZE_NORMAL = 13
    SIZE_SMALL = 12
    SIZE_TINY = 11
    SIZE_MICRO = 10
    
    # Font weights
    WEIGHT_LIGHT = 300
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    
    # Line heights
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.8


class Spacing:
    """Spacing constants for margins and padding."""
    
    # Standard spacing scale (in pixels)
    NONE = 0
    TINY = 4
    SMALL = 8
    MEDIUM = 12
    NORMAL = 16
    LARGE = 20
    XLARGE = 24
    HUGE = 32
    MASSIVE = 48
    
    # Specific use cases
    CARD_PADDING = 20
    BUTTON_PADDING_V = 8
    BUTTON_PADDING_H = 16
    INPUT_PADDING = 10
    DIALOG_MARGIN = 20
    SECTION_SPACING = 30
    FORM_ROW_SPACING = 15


class Borders:
    """Border styling constants."""
    
    # Border widths
    WIDTH_THIN = 1
    WIDTH_NORMAL = 2
    WIDTH_THICK = 4
    WIDTH_EXTRA_THICK = 6
    
    # Border radius
    RADIUS_NONE = 0
    RADIUS_SMALL = 4
    RADIUS_NORMAL = 6
    RADIUS_LARGE = 8
    RADIUS_XLARGE = 12
    RADIUS_ROUND = 50  # For circular elements
    
    # Border styles
    STYLE_SOLID = "solid"
    STYLE_DASHED = "dashed"
    STYLE_DOTTED = "dotted"


class Shadows:
    """Box shadow definitions."""
    
    NONE = "none"
    SMALL = "0 1px 3px rgba(0, 0, 0, 0.12)"
    NORMAL = "0 2px 6px rgba(0, 0, 0, 0.16)"
    MEDIUM = "0 4px 12px rgba(0, 0, 0, 0.15)"
    LARGE = "0 8px 24px rgba(0, 0, 0, 0.20)"
    XLARGE = "0 12px 48px rgba(0, 0, 0, 0.25)"


class Sizes:
    """Standard size constants for UI elements."""
    
    # Button sizes
    BUTTON_HEIGHT_SMALL = 32
    BUTTON_HEIGHT_NORMAL = 40
    BUTTON_HEIGHT_LARGE = 48
    BUTTON_MIN_WIDTH = 100
    
    # Input sizes
    INPUT_HEIGHT_SMALL = 32
    INPUT_HEIGHT_NORMAL = 40
    INPUT_HEIGHT_LARGE = 48
    
    # Icon sizes
    ICON_SMALL = 16
    ICON_NORMAL = 24
    ICON_LARGE = 32
    ICON_XLARGE = 48
    
    # Card sizes
    CARD_MIN_WIDTH = 180
    CARD_MIN_HEIGHT = 120
    CARD_MAX_WIDTH = 400
    
    # Dialog sizes
    DIALOG_MIN_WIDTH = 500
    DIALOG_MAX_WIDTH = 800
    
    # Table row height
    TABLE_ROW_HEIGHT = 40


class Transitions:
    """Animation and transition constants."""
    
    # Duration (in milliseconds)
    DURATION_FAST = 150
    DURATION_NORMAL = 250
    DURATION_SLOW = 350
    
    # Easing functions
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    EASE_LINEAR = "linear"


class StyleSheets:
    """Pre-built stylesheet strings for common components."""
    
    @staticmethod
    def button_primary(custom_color: str = None) -> str:
        """Primary button style."""
        color = custom_color or Colors.PRIMARY
        color_dark = Colors.PRIMARY_DARK if not custom_color else color
        
        return f"""
            QPushButton {{
                background-color: {color};
                color: {Colors.TEXT_LIGHT};
                padding: {Spacing.BUTTON_PADDING_V}px {Spacing.BUTTON_PADDING_H}px;
                border: none;
                border-radius: {Borders.RADIUS_NORMAL}px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_NORMAL}px;
            }}
            QPushButton:hover {{
                background-color: {color_dark};
            }}
            QPushButton:pressed {{
                background-color: {color_dark};
                padding-top: {Spacing.BUTTON_PADDING_V + 1}px;
            }}
            QPushButton:disabled {{
                background-color: {Colors.GREY_LIGHT};
                color: {Colors.GREY};
            }}
        """
    
    @staticmethod
    def button_secondary() -> str:
        """Secondary button style."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.PRIMARY};
                padding: {Spacing.BUTTON_PADDING_V}px {Spacing.BUTTON_PADDING_H}px;
                border: {Borders.WIDTH_NORMAL}px solid {Colors.PRIMARY};
                border-radius: {Borders.RADIUS_NORMAL}px;
                font-weight: {Fonts.WEIGHT_MEDIUM};
                font-size: {Fonts.SIZE_NORMAL}px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_LIGHT};
            }}
            QPushButton:disabled {{
                border-color: {Colors.GREY_LIGHT};
                color: {Colors.GREY};
            }}
        """
    
    @staticmethod
    def card(border_color: str = Colors.PRIMARY) -> str:
        """Card style."""
        return f"""
            QFrame {{
                background-color: {Colors.BG_PRIMARY};
                border-left: {Borders.WIDTH_EXTRA_THICK}px solid {border_color};
                border-radius: {Borders.RADIUS_NORMAL}px;
                padding: {Spacing.CARD_PADDING}px;
            }}
        """
    
    @staticmethod
    def input_field() -> str:
        """Input field style."""
        return f"""
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                padding: {Spacing.INPUT_PADDING}px;
                border: {Borders.WIDTH_THIN}px solid {Colors.BORDER_MEDIUM};
                border-radius: {Borders.RADIUS_SMALL}px;
                background-color: {Colors.BG_PRIMARY};
                font-size: {Fonts.SIZE_NORMAL}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {Colors.PRIMARY};
                outline: none;
            }}
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def table() -> str:
        """Table style."""
        return f"""
            QTableWidget {{
                background-color: {Colors.BG_PRIMARY};
                alternate-background-color: {Colors.BG_SECONDARY};
                border: {Borders.WIDTH_THIN}px solid {Colors.BORDER_LIGHT};
                gridline-color: {Colors.BORDER_LIGHT};
                font-size: {Fonts.SIZE_NORMAL}px;
            }}
            QTableWidget::item {{
                padding: {Spacing.SMALL}px;
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.BG_SELECTED};
                color: {Colors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Colors.GREY_LIGHTER};
                padding: {Spacing.MEDIUM}px;
                border: none;
                border-bottom: {Borders.WIDTH_NORMAL}px solid {Colors.BORDER_MEDIUM};
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_NORMAL}px;
            }}
        """
    
    @staticmethod
    def status_badge(status: str) -> str:
        """Status badge style based on status type."""
        status_colors = {
            'verified': (Colors.SUCCESS, Colors.SUCCESS_LIGHT),
            'pending': (Colors.WARNING, Colors.WARNING_LIGHT),
            'rejected': (Colors.ERROR, Colors.ERROR_LIGHT),
        }
        
        color, bg_color = status_colors.get(status.lower(), (Colors.GREY, Colors.GREY_LIGHT))
        
        return f"""
            QLabel {{
                background-color: {bg_color};
                color: {color};
                padding: {Spacing.TINY}px {Spacing.SMALL}px;
                border-radius: {Borders.RADIUS_SMALL}px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-size: {Fonts.SIZE_SMALL}px;
            }}
        """
    
    @staticmethod
    def alert_box(alert_type: str = 'info') -> str:
        """Alert box style."""
        alert_styles = {
            'success': (Colors.ALERT_SUCCESS_BG, Colors.ALERT_SUCCESS_BORDER, Colors.ALERT_SUCCESS_TEXT),
            'warning': (Colors.ALERT_WARNING_BG, Colors.ALERT_WARNING_BORDER, Colors.ALERT_WARNING_TEXT),
            'error': (Colors.ALERT_ERROR_BG, Colors.ALERT_ERROR_BORDER, Colors.ALERT_ERROR_TEXT),
            'info': (Colors.ALERT_INFO_BG, Colors.ALERT_INFO_BORDER, Colors.ALERT_INFO_TEXT),
        }
        
        bg, border, text = alert_styles.get(alert_type, alert_styles['info'])
        
        return f"""
            QFrame {{
                background-color: {bg};
                border-left: {Borders.WIDTH_THICK}px solid {border};
                border-radius: {Borders.RADIUS_NORMAL}px;
                padding: {Spacing.NORMAL}px;
            }}
            QLabel {{
                color: {text};
                font-size: {Fonts.SIZE_NORMAL}px;
            }}
        """


class IconStyles:
    """Icon styling and emoji mappings."""
    
    # Status icons
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"
    
    # Action icons
    ADD = "➕"
    EDIT = "✏️"
    DELETE = "🗑️"
    SAVE = "💾"
    REFRESH = "🔄"
    SEARCH = "🔍"
    FILTER = "🔽"
    PRINT = "🖨️"
    EXPORT = "📤"
    IMPORT = "📥"
    
    # Entity icons
    PRODUCT = "📦"
    PURCHASE_ORDER = "📋"
    COUPON = "🎫"
    MEDICAL_CENTRE = "🏥"
    LOCATION = "📍"
    USER = "👤"
    CALENDAR = "📅"
    
    # Status icons
    VERIFIED = "✅"
    PENDING = "⏳"
    REJECTED = "❌"
    
    # Dashboard icons
    DASHBOARD = "📊"
    REPORTS = "📈"
    SETTINGS = "⚙️"
    HELP = "❓"


# Utility functions
def get_status_color(status: str) -> str:
    """Get color for a given status."""
    status_lower = status.lower()
    if status_lower in ['verified', 'success', 'complete']:
        return Colors.SUCCESS
    elif status_lower in ['pending', 'warning', 'in_progress']:
        return Colors.WARNING
    elif status_lower in ['rejected', 'error', 'failed']:
        return Colors.ERROR
    else:
        return Colors.GREY


def get_card_color(entity_type: str) -> str:
    """Get color for a card based on entity type."""
    card_colors = {
        'products': Colors.CARD_PRODUCTS,
        'pos': Colors.CARD_POS,
        'coupons': Colors.CARD_COUPONS,
        'verified': Colors.CARD_VERIFIED,
        'pending': Colors.CARD_PENDING,
        'centres': Colors.CARD_CENTRES,
        'locations': Colors.CARD_LOCATIONS,
    }
    return card_colors.get(entity_type.lower(), Colors.PRIMARY)


def apply_hover_effect(base_color: str, darken_amount: int = 20) -> str:
    """
    Generate a darker version of a color for hover effects.
    
    Args:
        base_color: Hex color string (e.g., "#3498db")
        darken_amount: Amount to darken (0-100)
        
    Returns:
        Darker hex color string
    """
    # Simple darkening - multiply RGB values by factor
    # This is a basic implementation; for production, use a proper color library
    if not base_color.startswith('#'):
        return base_color
    
    try:
        # Remove # and convert to RGB
        hex_color = base_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Darken
        factor = (100 - darken_amount) / 100
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return base_color


# Export main style constants
__all__ = [
    'Colors',
    'Fonts',
    'Spacing',
    'Borders',
    'Shadows',
    'Sizes',
    'Transitions',
    'StyleSheets',
    'IconStyles',
    'get_status_color',
    'get_card_color',
    'apply_hover_effect',
]
