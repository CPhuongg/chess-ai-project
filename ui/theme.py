"""Shared visual tokens and stylesheet helpers for the PyQt UI."""

from PyQt5.QtGui import QColor, QPalette


FONT_FAMILY = "Arial"
MONO_FONT = "'Courier New', monospace"

COLORS = {
    "app_bg": "#202A33",
    "surface": "#26323D",
    "surface_alt": "#303D49",
    "panel": "#1F2932",
    "panel_alt": "#26313A",
    "border": "#3B4A55",
    "text": "#F1F5F2",
    "muted": "#9AA7A0",
    "disabled": "#5E6A66",
    "accent": "#769656",
    "accent_hover": "#86A867",
    "danger": "#C94A3A",
    "danger_hover": "#D65A49",
    "warning": "#D4A72C",
    "info": "#3E7FA8",
    "button": "#33414B",
    "button_hover": "#40505B",
    "button_pressed": "#27323A",
    "light_square": "#F0D9B5",
    "dark_square": "#B58863",
    "highlight": "#D6D06A",
    "valid_move": "#4F7F45",
    "castle": "#3E7FA8",
    "en_passant": "#D89632",
    "check": "#D94A4A",
    "white_piece": "#FFFFFF",
    "black_piece": "#111111",
}


def color(name: str) -> str:
    return COLORS[name]


def qcolor(name: str) -> QColor:
    return QColor(color(name))


def lighten(hex_color: str, amount: int = 115) -> str:
    return QColor(hex_color).lighter(amount).name()


def darken(hex_color: str, amount: int = 115) -> str:
    return QColor(hex_color).darker(amount).name()


def apply_app_palette(app) -> None:
    palette = QPalette()
    palette.setColor(QPalette.Window, qcolor("app_bg"))
    palette.setColor(QPalette.WindowText, qcolor("text"))
    palette.setColor(QPalette.Base, qcolor("panel"))
    palette.setColor(QPalette.AlternateBase, qcolor("panel_alt"))
    palette.setColor(QPalette.Text, qcolor("text"))
    palette.setColor(QPalette.BrightText, qcolor("text"))
    palette.setColor(QPalette.Button, qcolor("button"))
    palette.setColor(QPalette.ButtonText, qcolor("text"))
    palette.setColor(QPalette.Highlight, qcolor("accent"))
    palette.setColor(QPalette.HighlightedText, qcolor("text"))
    palette.setColor(QPalette.ToolTipBase, qcolor("panel"))
    palette.setColor(QPalette.ToolTipText, qcolor("text"))
    palette.setColor(QPalette.Disabled, QPalette.Text, qcolor("disabled"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, qcolor("disabled"))
    app.setPalette(palette)


def button_stylesheet(
    background: str | None = None,
    *,
    text: str | None = None,
    border: str | None = None,
    radius: int = 4,
) -> str:
    bg = background or color("button")
    fg = text or color("text")
    bd = border or lighten(bg, 125)
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            font-family: {MONO_FONT};
            font-size: 10pt;
            font-weight: bold;
            border: 1px solid {bd};
            border-radius: {radius}px;
            padding: 6px 10px;
        }}
        QPushButton:hover {{
            background-color: {lighten(bg, 112)};
            border-color: {color("accent")};
        }}
        QPushButton:pressed {{
            background-color: {darken(bg, 112)};
        }}
        QPushButton:disabled {{
            background-color: {color("panel_alt")};
            color: {color("disabled")};
            border-color: {color("border")};
        }}
    """


def section_label_stylesheet() -> str:
    return f"""
        font-family: {MONO_FONT};
        font-size: 8pt;
        font-weight: bold;
        color: {color("muted")};
        letter-spacing: 1px;
        padding: 4px 0 2px 0;
        background: transparent;
    """


def value_label_stylesheet() -> str:
    return f"""
        font-family: {MONO_FONT};
        font-size: 9pt;
        color: {color("text")};
        background-color: {color("panel")};
        border: 1px solid {color("border")};
        border-radius: 3px;
        padding: 5px 7px;
    """
