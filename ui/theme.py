"""Shared visual theme for the PyQt chess interface."""

from PyQt5.QtGui import QColor

FONT_UI = "'Segoe UI', 'Arial', sans-serif"
FONT_MONO = "'Cascadia Mono', 'Consolas', monospace"

APP_BG = "#101820"
SURFACE = "#17212B"
SURFACE_2 = "#1F2D3A"
SURFACE_3 = "#263847"
BORDER = "#314657"
BORDER_SOFT = "#263744"

TEXT = "#F4F7FA"
TEXT_MUTED = "#9FB0BF"
TEXT_DIM = "#6F8292"

ACCENT = "#4FB477"
ACCENT_HOVER = "#63C789"
ACCENT_BLUE = "#4EA3D8"
WARNING = "#D9A441"
DANGER = "#D65A4A"

BOARD_LIGHT = "#E9D8B8"
BOARD_DARK = "#9D6F4C"
BOARD_SELECTED = "#F0CC5A"
BOARD_LAST_MOVE = "#D9C95C"
VALID_MOVE = "#2F8F5B"
CHECK = "#D94F45"

WHITE_PIECE = "#FFF1C7"
BLACK_PIECE = "#1C252E"


def lighten(color: str, factor: int = 112) -> str:
    return QColor(color).lighter(factor).name()


def darken(color: str, factor: int = 115) -> str:
    return QColor(color).darker(factor).name()


def button_style(bg: str, *, text: str = TEXT, border: str | None = None) -> str:
    border = border or lighten(bg, 125)
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {text};
            font-family: {FONT_UI};
            font-size: 10pt;
            font-weight: 700;
            border: 1px solid {border};
            border-radius: 6px;
            padding: 7px 12px;
            letter-spacing: 0px;
        }}
        QPushButton:hover {{
            background-color: {lighten(bg, 112)};
            border-color: {lighten(border, 125)};
        }}
        QPushButton:pressed {{
            background-color: {darken(bg, 118)};
        }}
        QPushButton:disabled {{
            background-color: {SURFACE_2};
            color: {TEXT_DIM};
            border-color: {BORDER_SOFT};
        }}
    """


def ghost_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT_MUTED};
            font-family: {FONT_UI};
            font-size: 10pt;
            font-weight: 700;
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 7px 12px;
        }}
        QPushButton:hover {{
            color: {TEXT};
            background-color: {SURFACE_2};
            border-color: {ACCENT};
        }}
        QPushButton:pressed {{
            background-color: {SURFACE_3};
        }}
    """


def panel_style(radius: int = 8) -> str:
    return f"""
        background-color: {SURFACE};
        border: 1px solid {BORDER_SOFT};
        border-radius: {radius}px;
    """
