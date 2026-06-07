# Path: ui/components/load_game_dialog.py
# Description:
# Frameless, draggable dialog for loading saved .chess game files.
# Scans Desktop for existing .chess files and displays them in a list.
# Shows game preview info (mode, timestamp, move count, time control state, notes).
# Supports file browsing via native file dialog.
# Emits game_selected signal with loaded game data for the main board to restore.

import os
import json
import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QHBoxLayout, QFrame, QFileDialog, QSplitter, QWidget,
    QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

# ── Palette ────────────────────────────────────────────────────────────────
BG_DARK    = "#141414"
PANEL_BG   = "#1E1E1E"
PANEL2     = "#242424"
BORDER_CLR = "#383838"
ACCENT_GRN = "#769656"
ACCENT_RED = "#C1392B"
TEXT_MAIN  = "#EFEFEF"
TEXT_DIM   = "#888888"
LIST_BG    = "#1A1A1A"
LIST_SEL   = "#2A3A2A"
_MONO      = "'Courier New', monospace"
# ───────────────────────────────────────────────────────────────────────────


def _section(text):
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(f"""
        font-family: {_MONO};
        font-size: 8pt;
        color: {TEXT_DIM};
        letter-spacing: 2px;
        padding: 4px 0px 2px 0px;
        background: transparent;
    """)
    return lbl


class LoadGameDialog(QDialog):
    """Dialog tải game đã lưu — dark, terminal-inspired."""

    game_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Game")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setFixedSize(640, 460)
        self.setStyleSheet(f"background-color: {PANEL_BG};")
        self._drag_pos = None
        self.game_data = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Title bar ──────────────────────────────────────────────────────
        title_bar = QFrame()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_DARK};
                border-bottom: 1px solid {ACCENT_GRN};
            }}
        """)
        tbl = QHBoxLayout(title_bar)
        tbl.setContentsMargins(12, 0, 12, 0)
        lbl = QLabel("  LOAD SAVED GAME")
        lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 10pt;
            font-weight: bold;
            color: {ACCENT_GRN};
            letter-spacing: 2px;
        """)
        tbl.addWidget(lbl)
        tbl.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: none;
                font-size: 12pt;
            }}
            QPushButton:hover {{ color: {TEXT_MAIN}; }}
        """)
        close_btn.clicked.connect(self.reject)
        tbl.addWidget(close_btn)
        outer.addWidget(title_bar)

        # ── Content ────────────────────────────────────────────────────────
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 12, 16, 10)
        cl.setSpacing(8)

        # Browse button row
        browse_row = QHBoxLayout()
        browse_row.addWidget(_section("file"))
        browse_row.addStretch()
        browse_btn = QPushButton("📂  BROWSE...")
        browse_btn.setFixedHeight(28)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {_MONO};
                font-size: 9pt;
                color: {TEXT_DIM};
                background: transparent;
                border: 1px solid {BORDER_CLR};
                border-radius: 2px;
                padding: 2px 10px;
            }}
            QPushButton:hover {{ color: {TEXT_MAIN}; border-color: #555; }}
        """)
        browse_btn.clicked.connect(self._browse)
        browse_row.addWidget(browse_btn)
        cl.addLayout(browse_row)

        # Recent games list
        cl.addWidget(_section("recent saves"))
        self.game_list = QListWidget()
        self.game_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {LIST_BG};
                border: 1px solid {BORDER_CLR};
                font-family: {_MONO};
                font-size: 10pt;
                color: {TEXT_MAIN};
                outline: none;
                padding: 0px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #252525;
                min-height: 24px;
            }}
            QListWidget::item:selected {{
                background-color: {LIST_SEL};
                color: {TEXT_MAIN};
            }}
            QListWidget::item:hover {{
                background-color: #222222;
            }}
        """)
        self.game_list.itemClicked.connect(self._on_select)
        self.game_list.itemDoubleClicked.connect(self._on_double_click)
        cl.addWidget(self.game_list)

        # Info preview
        cl.addWidget(_section("game info"))
        self.info_label = QLabel("Select a game file to preview info...")
        self.info_label.setWordWrap(True)
        self.info_label.setFixedHeight(70)
        self.info_label.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 9pt;
            color: {TEXT_DIM};
            background-color: {LIST_BG};
            border: 1px solid {BORDER_CLR};
            padding: 8px;
        """)
        cl.addWidget(self.info_label)

        outer.addWidget(content)

        # ── Button bar ─────────────────────────────────────────────────────
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_DARK};
                border-top: 1px solid {BORDER_CLR};
            }}
        """)
        bfl = QHBoxLayout(btn_frame)
        bfl.setContentsMargins(16, 8, 16, 8)
        bfl.setSpacing(8)

        self.load_btn = QPushButton("▶  LOAD GAME")
        self.load_btn.setFixedHeight(34)
        self.load_btn.setEnabled(False)
        self.load_btn.setCursor(Qt.PointingHandCursor)
        self.load_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {_MONO};
                font-size: 10pt;
                font-weight: bold;
                color: {TEXT_MAIN};
                background-color: {ACCENT_GRN};
                border: none;
                border-radius: 2px;
                padding: 4px 16px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background-color: {QColor(ACCENT_GRN).lighter(115).name()}; }}
            QPushButton:disabled {{ background-color: #2A3A2A; color: #555; }}
        """)
        self.load_btn.clicked.connect(self._load_selected)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {_MONO};
                font-size: 10pt;
                font-weight: bold;
                color: {TEXT_DIM};
                background: transparent;
                border: 1px solid {BORDER_CLR};
                border-radius: 2px;
                padding: 4px 16px;
            }}
            QPushButton:hover {{ color: {TEXT_MAIN}; border-color: #555; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        bfl.addStretch()
        bfl.addWidget(self.load_btn)
        bfl.addWidget(cancel_btn)
        outer.addWidget(btn_frame)

        self._populate_recent()

    # ── drag ───────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.pos().y() < 36:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)
    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    # ── internals ──────────────────────────────────────────────────────────
    def _populate_recent(self):
        """Try to find .chess files on Desktop."""
        desktop = os.path.expanduser("~/Desktop")
        try:
            files = [f for f in os.listdir(desktop) if f.endswith('.chess')]
            for fname in sorted(files, reverse=True)[:20]:
                item = QListWidgetItem(f"  {fname}")
                item.setData(Qt.UserRole, os.path.join(desktop, fname))
                self.game_list.addItem(item)
        except Exception:
            pass
        if self.game_list.count() == 0:
            placeholder = QListWidgetItem("  No saved games found on Desktop")
            placeholder.setForeground(QColor(TEXT_DIM))
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsSelectable)
            self.game_list.addItem(placeholder)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Chess Game",
            os.path.expanduser("~/Desktop"),
            "Chess Game Files (*.chess);;All Files (*)"
        )
        if path:
            self._load_file(path)

    def _on_select(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self._preview(path)
            self.load_btn.setEnabled(True)

    def _on_double_click(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self._load_file(path)

    def _preview(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            mode  = data.get('mode', '?')
            ts    = data.get('timestamp', '?')
            moves = len(data.get('move_history', []))
            name  = data.get('game_name', os.path.basename(path))
            timer = data.get('timer_settings', {})
            tinfo = "No time control"
            if timer.get('enabled'):
                w = timer.get('white_time_ms', 0) // 1000
                b = timer.get('black_time_ms', 0) // 1000
                tinfo = f"White {w//60}:{w%60:02d}  /  Black {b//60}:{b%60:02d}"
            lines = [
                f"Name:    {name}",
                f"Mode:    {mode}    |    Moves: {moves}    |    Saved: {ts}",
                f"Clock:   {tinfo}",
            ]
            notes = data.get('game_notes', '')
            if notes:
                lines.append(f"Notes:   {notes[:80]}")
            self.info_label.setText("\n".join(lines))
            self.info_label.setStyleSheet(f"""
                font-family: {_MONO};
                font-size: 9pt;
                color: {TEXT_MAIN};
                background-color: {LIST_BG};
                border: 1px solid {ACCENT_GRN};
                padding: 8px;
            """)
            self._selected_path = path
        except Exception as e:
            self.info_label.setText(f"Error reading file: {e}")

    def _load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            required = ['fen', 'mode', 'turn', 'move_history']
            if not all(k in data for k in required):
                QMessageBox.warning(self, "Invalid File",
                    "This file is missing required game data.")
                return
            self.game_data = data
            self.game_selected.emit(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load: {e}")

    def _load_selected(self):
        item = self.game_list.currentItem()
        if item:
            path = item.data(Qt.UserRole)
            if path:
                self._load_file(path)