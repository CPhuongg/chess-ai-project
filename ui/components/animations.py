"""Smooth chess-piece animations built on PyQt property animations."""

from PyQt5.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect, QGraphicsOpacityEffect

from utils.config import Config


def _animation_duration(duration=None) -> int:
    base = duration if duration is not None else Config.DEFAULT_ANIMATION_DURATION
    return max(180, int(base))


def _target_rect(widget, target) -> QRect:
    if isinstance(target, QRect):
        return target
    if isinstance(target, QPoint):
        return QRect(target, widget.size())
    raise TypeError("target must be QPoint or QRect")


class AnimatedLabel(QLabel):
    """Temporary overlay label used for piece movement."""

    animation_finished = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.animation = QPropertyAnimation(self, b"geometry", self)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(_animation_duration())
        self.animation.finished.connect(self.on_animation_finished)

        self._is_animating = False
        self._add_shadow()

    def _add_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

    def move_to(self, target, duration=None):
        """Animate to a QPoint or QRect target."""
        if self._is_animating:
            self.animation.stop()

        self.animation.setDuration(_animation_duration(duration))
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(_target_rect(self, target))
        self._is_animating = True
        self.raise_()
        self.animation.start()

    def on_animation_finished(self):
        self._is_animating = False
        self.animation_finished.emit()

    def cancel_animation(self):
        if self._is_animating:
            self.animation.stop()
            self._is_animating = False


def _make_opacity_animation(widget, duration):
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(1.0)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(_animation_duration(duration))
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.InOutQuad)
    return animation


def _make_shrink_animation(widget, duration):
    rect = widget.geometry()
    end_width = max(1, int(rect.width() * 0.2))
    end_height = max(1, int(rect.height() * 0.2))
    end_rect = QRect(
        rect.center().x() - end_width // 2,
        rect.center().y() - end_height // 2,
        end_width,
        end_height,
    )

    animation = QPropertyAnimation(widget, b"geometry")
    animation.setDuration(_animation_duration(duration))
    animation.setStartValue(rect)
    animation.setEndValue(end_rect)
    animation.setEasingCurve(QEasingCurve.InOutCubic)
    return animation


class CaptureAnimation(QParallelAnimationGroup):
    """Fade and shrink a captured piece without abrupt geometry collapse."""

    def __init__(self, piece_label, parent=None):
        super().__init__(parent)
        self.piece_label = piece_label
        duration = max(180, Config.DEFAULT_ANIMATION_DURATION - 40)

        self.addAnimation(_make_shrink_animation(piece_label, duration))
        self.addAnimation(_make_opacity_animation(piece_label, duration))
        self.finished.connect(self._cleanup)

    def _cleanup(self):
        self.piece_label.hide()
        self.piece_label.deleteLater()


class EnPassantAnimation(QParallelAnimationGroup):
    """Move one piece while fading the captured en-passant pawn."""

    def __init__(self, moving_piece, captured_piece, target_pos, parent=None):
        super().__init__(parent)
        self.captured_piece = captured_piece
        duration = _animation_duration()

        move_animation = QPropertyAnimation(moving_piece, b"geometry")
        move_animation.setDuration(duration)
        move_animation.setStartValue(moving_piece.geometry())
        move_animation.setEndValue(_target_rect(moving_piece, target_pos))
        move_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.addAnimation(move_animation)
        self.addAnimation(_make_shrink_animation(captured_piece, duration))
        self.addAnimation(_make_opacity_animation(captured_piece, duration))
        self.finished.connect(self._cleanup)

    def _cleanup(self):
        self.captured_piece.hide()
        self.captured_piece.deleteLater()


class CastlingAnimation(QParallelAnimationGroup):
    """Move king and rook together during castling."""

    def __init__(self, king_label, rook_label, king_target, rook_target, parent=None):
        super().__init__(parent)
        duration = _animation_duration()

        king_animation = QPropertyAnimation(king_label, b"geometry")
        king_animation.setDuration(duration)
        king_animation.setStartValue(king_label.geometry())
        king_animation.setEndValue(_target_rect(king_label, king_target))
        king_animation.setEasingCurve(QEasingCurve.OutCubic)

        rook_animation = QPropertyAnimation(rook_label, b"geometry")
        rook_animation.setDuration(duration)
        rook_animation.setStartValue(rook_label.geometry())
        rook_animation.setEndValue(_target_rect(rook_label, rook_target))
        rook_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.addAnimation(king_animation)
        self.addAnimation(rook_animation)
