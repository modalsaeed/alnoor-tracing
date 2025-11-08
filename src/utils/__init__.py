"""Utilities package initialization."""

from .validators import (
    ValidationError,
    ValidationConstants,
    validate_cpr,
    validate_reference,
    validate_po_reference,
    validate_quantity,
    validate_name,
    validate_phone,
    validate_email,
    validate_date_range,
    validate_required_field,
    sanitize_input,
    normalize_reference,
)

from .style_constants import (
    Colors,
    Fonts,
    Spacing,
    Borders,
    Shadows,
    Sizes,
    Transitions,
    StyleSheets,
    IconStyles,
    get_status_color,
    get_card_color,
    apply_hover_effect,
)

__all__ = [
    # Validators
    "ValidationError",
    "ValidationConstants",
    "validate_cpr",
    "validate_reference",
    "validate_po_reference",
    "validate_quantity",
    "validate_name",
    "validate_phone",
    "validate_email",
    "validate_date_range",
    "validate_required_field",
    "sanitize_input",
    "normalize_reference",
    # Style Constants
    "Colors",
    "Fonts",
    "Spacing",
    "Borders",
    "Shadows",
    "Sizes",
    "Transitions",
    "StyleSheets",
    "IconStyles",
    "get_status_color",
    "get_card_color",
    "apply_hover_effect",
]
