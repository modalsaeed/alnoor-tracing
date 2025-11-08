"""
Style Constants Usage Examples

This file demonstrates how to use the centralized style constants
in your PyQt6 components.
"""

from PyQt6.QtWidgets import QPushButton, QLabel, QFrame, QLineEdit
from utils import Colors, Fonts, Spacing, Borders, StyleSheets, IconStyles


def example_button_primary():
    """Create a primary button with consistent styling."""
    button = QPushButton(f"{IconStyles.SAVE} Save")
    button.setStyleSheet(StyleSheets.button_primary())
    button.setMinimumWidth(100)
    return button


def example_button_success():
    """Create a success button (green)."""
    button = QPushButton(f"{IconStyles.SUCCESS} Verify")
    button.setStyleSheet(StyleSheets.button_primary(Colors.SUCCESS))
    button.setMinimumWidth(100)
    return button


def example_button_secondary():
    """Create a secondary button."""
    button = QPushButton(f"{IconStyles.REFRESH} Cancel")
    button.setStyleSheet(StyleSheets.button_secondary())
    button.setMinimumWidth(100)
    return button


def example_metric_card():
    """Create a metric card like in the dashboard."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {Colors.BG_PRIMARY};
            border-left: {Borders.WIDTH_EXTRA_THICK}px solid {Colors.CARD_PRODUCTS};
            border-radius: {Borders.RADIUS_NORMAL}px;
            padding: {Spacing.CARD_PADDING}px;
            min-width: 180px;
            min-height: 120px;
        }}
    """)
    return card


def example_status_label(status: str):
    """Create a status label with appropriate color."""
    from utils import get_status_color
    
    label = QLabel(status.upper())
    color = get_status_color(status)
    
    label.setStyleSheet(f"""
        QLabel {{
            background-color: {color};
            color: {Colors.TEXT_LIGHT};
            padding: {Spacing.TINY}px {Spacing.MEDIUM}px;
            border-radius: {Borders.RADIUS_SMALL}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            font-size: {Fonts.SIZE_SMALL}px;
        }}
    """)
    return label


def example_input_field():
    """Create a styled input field."""
    input_field = QLineEdit()
    input_field.setPlaceholderText("Enter text...")
    input_field.setStyleSheet(StyleSheets.input_field())
    return input_field


def example_alert_box(message: str, alert_type: str = 'info'):
    """Create an alert box."""
    alert = QFrame()
    alert.setStyleSheet(StyleSheets.alert_box(alert_type))
    
    # Add icon based on type
    icon_map = {
        'success': IconStyles.SUCCESS,
        'warning': IconStyles.WARNING,
        'error': IconStyles.ERROR,
        'info': IconStyles.INFO,
    }
    icon = icon_map.get(alert_type, IconStyles.INFO)
    
    label = QLabel(f"{icon} {message}")
    label.setWordWrap(True)
    
    return alert, label


def example_custom_styling():
    """
    Example of custom styling using constants.
    
    Instead of hardcoding values:
        BAD: setStyleSheet("padding: 15px; color: #3498db;")
    
    Use constants:
        GOOD: setStyleSheet(f"padding: {Spacing.NORMAL}px; color: {Colors.PRIMARY};")
    """
    widget = QFrame()
    widget.setStyleSheet(f"""
        QFrame {{
            background-color: {Colors.BG_PRIMARY};
            border: {Borders.WIDTH_THIN}px solid {Colors.BORDER_MEDIUM};
            border-radius: {Borders.RADIUS_NORMAL}px;
            padding: {Spacing.NORMAL}px;
            margin: {Spacing.SMALL}px;
        }}
        QFrame:hover {{
            border-color: {Colors.PRIMARY};
            background-color: {Colors.BG_HOVER};
        }}
    """)
    return widget


def example_title_label():
    """Create a title label with consistent styling."""
    title = QLabel(f"{IconStyles.DASHBOARD} Dashboard")
    title.setStyleSheet(f"""
        QLabel {{
            font-size: {Fonts.SIZE_XLARGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            padding: {Spacing.MEDIUM}px 0;
        }}
    """)
    return title


def example_section_header():
    """Create a section header."""
    header = QLabel(f"{IconStyles.REPORTS} Recent Activity")
    header.setStyleSheet(f"""
        QLabel {{
            font-size: {Fonts.SIZE_LARGE}px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            padding: {Spacing.NORMAL}px 0;
            margin-top: {Spacing.SECTION_SPACING}px;
        }}
    """)
    return header


# Migration Guide
"""
MIGRATION GUIDE: Converting existing code to use style constants

BEFORE (hardcoded values):
----------------------------------------
button.setStyleSheet('''
    QPushButton {
        background-color: #27ae60;
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #229954;
    }
''')

AFTER (using constants):
----------------------------------------
from utils import Colors, Spacing, Borders, Fonts, StyleSheets

# Option 1: Use pre-built stylesheet
button.setStyleSheet(StyleSheets.button_primary(Colors.SUCCESS))

# Option 2: Use constants for custom styling
button.setStyleSheet(f'''
    QPushButton {{
        background-color: {Colors.SUCCESS};
        color: {Colors.TEXT_LIGHT};
        padding: {Spacing.BUTTON_PADDING_V}px {Spacing.BUTTON_PADDING_H}px;
        border-radius: {Borders.RADIUS_NORMAL}px;
        font-weight: {Fonts.WEIGHT_BOLD};
    }}
    QPushButton:hover {{
        background-color: {Colors.SUCCESS_DARK};
    }}
''')


BENEFITS:
1. ✅ Consistency: Same colors/spacing across entire app
2. ✅ Maintainability: Change once, updates everywhere
3. ✅ Readability: Colors.PRIMARY more meaningful than #3498db
4. ✅ Type hints: IDE autocomplete for all constants
5. ✅ Flexibility: Pre-built stylesheets + custom options


COMMON PATTERNS:
----------------------------------------

Pattern 1: Card with entity-specific color
    from utils import get_card_color
    
    card_color = get_card_color('products')  # Returns Colors.CARD_PRODUCTS
    card.setStyleSheet(StyleSheets.card(card_color))


Pattern 2: Status badge
    from utils import get_status_color
    
    status_color = get_status_color('verified')  # Returns Colors.SUCCESS
    badge.setStyleSheet(f"background: {status_color}; ...")


Pattern 3: Hover effects
    from utils import apply_hover_effect
    
    base = Colors.PRIMARY
    hover = apply_hover_effect(base, darken_amount=15)
    
    widget.setStyleSheet(f'''
        Widget {{ background: {base}; }}
        Widget:hover {{ background: {hover}; }}
    ''')


NEXT STEPS:
----------------------------------------
1. Update existing widgets to use StyleSheets.* helpers
2. Replace hardcoded colors with Colors.* constants
3. Replace hardcoded spacing with Spacing.* constants
4. Replace hardcoded fonts with Fonts.* constants
5. Use IconStyles.* for consistent emoji/icons


FILES TO UPDATE:
- src/ui/widgets/dashboard_widget.py
- src/ui/widgets/products_widget.py
- src/ui/widgets/purchase_orders_widget.py
- src/ui/widgets/coupons_widget.py
- src/ui/widgets/medical_centres_widget.py
- src/ui/widgets/distribution_locations_widget.py
- src/ui/widgets/reports_widget.py
- All dialog files in src/ui/dialogs/
"""
