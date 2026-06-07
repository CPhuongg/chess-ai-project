# Path: ui/components/animations.py
# Description:
# Animation components for chess piece movements using PyQt5's QPropertyAnimation.
# Provides AnimatedLabel for smooth piece transitions with easing curves and drop shadows.
# Includes specialized animations: CaptureAnimation (fade-out), EnPassantAnimation (parallel move + fade),
# and CastlingAnimation (sequential king + rook movement).
# Animation duration is configurable via Config.DEFAULT_ANIMATION_DURATION (default ~300ms).

from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import (
    QPropertyAnimation, QEasingCurve, QPoint, QSequentialAnimationGroup, 
    QParallelAnimationGroup, Qt, pyqtSignal
)
from PyQt5.QtGui import QColor

from utils.config import Config

class AnimatedLabel(QLabel):
    """
    Custom QLabel with animation capabilities for chess pieces.
    Provides smooth movement with proper cleanup upon completion.
    """
    
    animation_finished = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up animation properties
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(Config.DEFAULT_ANIMATION_DURATION)
        
        # Connect finished signal
        self.animation.finished.connect(self.on_animation_finished)
        
        # Track animation state
        self._is_animating = False
        
        # Add drop shadow for visual depth
        self._add_shadow()
    
    def _add_shadow(self):
        """Add a drop shadow to the piece for better visual appearance."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(3, 3)
        self.setGraphicsEffect(shadow)
        
    def move_to(self, target_pos, duration=None):
        """
        Animate movement to target position.
        
        Args:
            target_pos (QPoint): The target position to move to
            duration (int, optional): Custom animation duration in ms
        """
        if duration:
            self.animation.setDuration(duration)
            
        # Cancel any ongoing animation
        if self._is_animating:
            self.animation.stop()
            
        self._is_animating = True
        start_pos = self.pos()
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(target_pos)
        self.animation.start()
    
    def on_animation_finished(self):
        """Handle animation completion."""
        self._is_animating = False
        self.animation_finished.emit()
    
    def cancel_animation(self):
        """Cancel any ongoing animation."""
        if self._is_animating:
            self.animation.stop()
            self._is_animating = False

class CaptureAnimation(QSequentialAnimationGroup):
    """
    Animation for piece captures with specialized effects.
    Shows a captured piece being removed from the board with visual feedback.
    """
    
    def __init__(self, piece_label, parent=None):
        super().__init__(parent)
        self.piece_label = piece_label
        
        # Create fade out animation
        self.fade_out = QPropertyAnimation(piece_label, b"windowOpacity")
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setDuration(300)
        self.fade_out.setEasingCurve(QEasingCurve.OutQuad)
        
        # Add to animation group
        self.addAnimation(self.fade_out)
        
        # Connect finished signal
        self.finished.connect(self.cleanup)
    
    def cleanup(self):
        """Clean up after animation completes."""
        self.piece_label.hide()
        self.piece_label.deleteLater()
        
class EnPassantAnimation(QParallelAnimationGroup):
    """
    Specialized animation for en passant captures.
    Shows both the moving pawn and the captured pawn with appropriate effects.
    """
    
    def __init__(self, moving_piece, captured_piece, target_pos, parent=None):
        super().__init__(parent)
        self.moving_piece = moving_piece
        self.captured_piece = captured_piece
        
        # Create movement animation for the capturing pawn
        self.move_anim = QPropertyAnimation(moving_piece, b"pos")
        self.move_anim.setStartValue(moving_piece.pos())
        self.move_anim.setEndValue(target_pos)
        self.move_anim.setDuration(Config.DEFAULT_ANIMATION_DURATION)
        self.move_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Create fade out animation for the captured pawn
        self.fade_out = QPropertyAnimation(captured_piece, b"windowOpacity")
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setDuration(Config.DEFAULT_ANIMATION_DURATION)
        self.fade_out.setEasingCurve(QEasingCurve.OutQuad)
        
        # Add both animations to run in parallel
        self.addAnimation(self.move_anim)
        self.addAnimation(self.fade_out)
        
        # Connect finished signal
        self.finished.connect(self.cleanup)
    
    def cleanup(self):
        """Clean up after animation completes."""
        self.captured_piece.hide()
        self.captured_piece.deleteLater()

class CastlingAnimation(QSequentialAnimationGroup):
    """
    Animation for castling moves showing both king and rook movement.
    """
    
    def __init__(self, king_label, rook_label, king_target, rook_target, parent=None):
        super().__init__(parent)
        self.king_label = king_label
        self.rook_label = rook_label
        
        # Create parallel animation group for simultaneous movement
        parallel_group = QParallelAnimationGroup()
        
        # King animation
        king_anim = QPropertyAnimation(king_label, b"pos")
        king_anim.setStartValue(king_label.pos())
        king_anim.setEndValue(king_target)
        king_anim.setDuration(Config.DEFAULT_ANIMATION_DURATION)
        king_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Rook animation
        rook_anim = QPropertyAnimation(rook_label, b"pos")
        rook_anim.setStartValue(rook_label.pos())
        rook_anim.setEndValue(rook_target)
        rook_anim.setDuration(Config.DEFAULT_ANIMATION_DURATION)
        rook_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Add animations to the parallel group
        parallel_group.addAnimation(king_anim)
        parallel_group.addAnimation(rook_anim)
        
        # Add the parallel group to this sequential group
        self.addAnimation(parallel_group)