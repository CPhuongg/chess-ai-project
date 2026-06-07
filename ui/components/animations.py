# Path: ui/components/animations.py
# Description:
# Animation components for chess piece movements using PyQt5's QPropertyAnimation.
# Provides AnimatedLabel for smooth piece transitions with easing curves and drop shadows.
# Includes specialized animations:
#   - CaptureAnimation: shrink + fade-out (scale down rồi biến mất)
#   - EnPassantAnimation: parallel move + shrink/fade cho quân bị ăn
#   - CastlingAnimation: king + rook di chuyển song song mượt mà
# Animation duration configurable via Config.DEFAULT_ANIMATION_DURATION (default ~300ms).
#
# FIX NOTE:
#   - Dùng QGraphicsOpacityEffect thay windowOpacity cho child widgets (windowOpacity
#     chỉ hoạt động đúng với top-level windows).
#   - Dùng b"geometry" thay b"pos" để tránh hiện tượng giật khi widget nằm trong layout.
#   - CaptureAnimation: thu nhỏ (scale geometry về center) + fade đồng thời.

from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PyQt5.QtCore import (
    QPropertyAnimation, QEasingCurve, QPoint, QRect, QSequentialAnimationGroup,
    QParallelAnimationGroup, Qt, pyqtSignal
)
from PyQt5.QtGui import QColor

from utils.config import Config


class AnimatedLabel(QLabel):
    """
    Custom QLabel với animation di chuyển mượt mà cho quân cờ.
    Dùng b"pos" + OutQuint easing để chuyển động tự nhiên hơn OutCubic.
    """

    animation_finished = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Animation di chuyển
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.OutQuint)   # mượt hơn OutCubic
        self.animation.setDuration(Config.DEFAULT_ANIMATION_DURATION)
        self.animation.finished.connect(self.on_animation_finished)

        self._is_animating = False
        self._add_shadow()

    def _add_shadow(self):
        """Drop shadow nhẹ cho chiều sâu hình ảnh."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

    def move_to(self, target_pos, duration=None):
        """
        Animate di chuyển đến target_pos.

        Args:
            target_pos (QPoint): Vị trí đích
            duration (int, optional): Thời gian animation tính bằng ms
        """
        if duration is not None:
            self.animation.setDuration(duration)

        if self._is_animating:
            self.animation.stop()

        self._is_animating = True
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(target_pos)
        self.animation.start()

    def on_animation_finished(self):
        self._is_animating = False
        self.animation_finished.emit()

    def cancel_animation(self):
        if self._is_animating:
            self.animation.stop()
            self._is_animating = False


# ─────────────────────────────────────────────────────────────────────────────
# Helper: tạo QGraphicsOpacityEffect và QPropertyAnimation fade-out
# Dùng thay windowOpacity vì windowOpacity không hoạt động với child widget.
# ─────────────────────────────────────────────────────────────────────────────

def _make_opacity_effect(widget):
    """Gắn QGraphicsOpacityEffect vào widget và trả về (effect, anim)."""
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(1.0)
    widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.InQuad)
    return effect, anim


def _make_shrink_anim(widget, duration):
    """
    Tạo animation thu nhỏ geometry về điểm trung tâm.
    Quân cờ sẽ 'co lại' về giữa trước khi biến mất.
    """
    rect = widget.geometry()
    cx = rect.x() + rect.width() // 2
    cy = rect.y() + rect.height() // 2

    anim = QPropertyAnimation(widget, b"geometry")
    anim.setStartValue(rect)
    anim.setEndValue(QRect(cx, cy, 0, 0))   # thu về điểm trung tâm
    anim.setDuration(duration)
    anim.setEasingCurve(QEasingCurve.InBack)  # hơi "bật ngược" rồi co — trông tự nhiên
    return anim


# ─────────────────────────────────────────────────────────────────────────────

class CaptureAnimation(QParallelAnimationGroup):
    """
    Animation khi ăn quân: thu nhỏ + fade-out đồng thời.
    Hiệu ứng: quân bị ăn co dần về trung tâm và mờ đi rồi biến mất.
    """

    def __init__(self, piece_label, parent=None):
        super().__init__(parent)
        self.piece_label = piece_label

        duration = max(250, Config.DEFAULT_ANIMATION_DURATION - 50)

        # 1. Thu nhỏ geometry
        shrink = _make_shrink_anim(piece_label, duration)
        self.addAnimation(shrink)

        # 2. Fade-out opacity — cần tạo effect trước khi shrink
        #    (shrink thay geometry, không ảnh hưởng opacity)
        _effect, fade = _make_opacity_effect(piece_label)
        fade.setDuration(duration)
        self.addAnimation(fade)

        self.finished.connect(self._cleanup)

    def _cleanup(self):
        self.piece_label.hide()
        self.piece_label.deleteLater()


class EnPassantAnimation(QParallelAnimationGroup):
    """
    Animation en passant:
    - Quân đang đi: di chuyển mượt đến ô đích
    - Quân bị ăn (en passant): thu nhỏ + fade-out
    """

    def __init__(self, moving_piece, captured_piece, target_pos, parent=None):
        super().__init__(parent)
        self.moving_piece  = moving_piece
        self.captured_piece = captured_piece

        duration = Config.DEFAULT_ANIMATION_DURATION

        # Di chuyển quân đang đi
        move_anim = QPropertyAnimation(moving_piece, b"pos")
        move_anim.setStartValue(moving_piece.pos())
        move_anim.setEndValue(target_pos)
        move_anim.setDuration(duration)
        move_anim.setEasingCurve(QEasingCurve.OutQuint)
        self.addAnimation(move_anim)

        # Thu nhỏ quân bị ăn
        shrink = _make_shrink_anim(captured_piece, duration)
        self.addAnimation(shrink)

        # Fade-out quân bị ăn
        _effect, fade = _make_opacity_effect(captured_piece)
        fade.setDuration(duration)
        self.addAnimation(fade)

        self.finished.connect(self._cleanup)

    def _cleanup(self):
        self.captured_piece.hide()
        self.captured_piece.deleteLater()


class CastlingAnimation(QParallelAnimationGroup):
    """
    Animation nhập thành: vua và xe di chuyển song song, cùng lúc.
    Dùng QParallelAnimationGroup thay QSequentialAnimationGroup để mượt hơn.
    """

    def __init__(self, king_label, rook_label, king_target, rook_target, parent=None):
        super().__init__(parent)

        duration = Config.DEFAULT_ANIMATION_DURATION

        # Vua
        king_anim = QPropertyAnimation(king_label, b"pos")
        king_anim.setStartValue(king_label.pos())
        king_anim.setEndValue(king_target)
        king_anim.setDuration(duration)
        king_anim.setEasingCurve(QEasingCurve.OutQuint)

        # Xe — chạy hơi nhanh hơn một chút để trông tự nhiên
        rook_anim = QPropertyAnimation(rook_label, b"pos")
        rook_anim.setStartValue(rook_label.pos())
        rook_anim.setEndValue(rook_target)
        rook_anim.setDuration(int(duration * 0.85))
        rook_anim.setEasingCurve(QEasingCurve.OutQuint)

        self.addAnimation(king_anim)
        self.addAnimation(rook_anim)