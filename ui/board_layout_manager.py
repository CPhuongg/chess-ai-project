# Path: ui/board_layout_manager.py
# Description:
# Custom layout manager for the chess board that ensures a perfectly square playing area.
# SquareGridLayout inherits from QGridLayout and overrides setGeometry() to center
# the board and enforce equal cell sizes based on the smallest dimension.
# Includes 9x9 grid (8x8 squares + labels for ranks and files).
# Minimum cell size is 45px, default size hint is 540x540 pixels.
# Provides create_square_board_container() helper for aspect-ratio containers.

from PyQt5.QtWidgets import QGridLayout, QWidget, QSizePolicy
from PyQt5.QtCore import QRect, QSize, Qt

class SquareGridLayout(QGridLayout):
    """
    Custom grid layout that ensures chess board remains perfectly square.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)  # Remove margins
    
    def setGeometry(self, rect):
        """
        Override the geometry setting to enforce a perfect square board.
        
        Args:
            rect (QRect): The rectangle to set as the layout's geometry
        """
        # Determine the smallest dimension to create a perfect square
        min_dimension = min(rect.width(), rect.height())
        
        # Center the square layout within the available rectangle
        x_offset = (rect.width() - min_dimension) // 2
        y_offset = (rect.height() - min_dimension) // 2
        
        # Create a square rectangle
        square_rect = QRect(
            rect.x() + x_offset, 
            rect.y() + y_offset, 
            min_dimension, 
            min_dimension
        )
        
        # Call the parent setGeometry with the square rectangle
        super().setGeometry(square_rect)
        
        # Calculate cell size (divide equally among 9 rows/columns to include labels)
        cell_size = min_dimension // 9
        
        # Đảm bảo cell_size không quá nhỏ
        if cell_size < 40:
            cell_size = 40
        
        # Adjust items within the layout
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.itemAtPosition(row, col)
                if item and item.widget():
                    # Position labels and squares precisely
                    x = square_rect.x() + col * cell_size
                    y = square_rect.y() + row * cell_size
                    
                    # Size items to exactly fill their grid cell
                    item.widget().setGeometry(
                        x, 
                        y, 
                        cell_size, 
                        cell_size
                    )
    
    def minimumSize(self):
        """
        Return the minimum size for the layout, maintaining square aspect.
        """
        # Calculate minimum cell size
        min_cell_size = 45  # TĂNG minimum size lên 45
        total_min_size = min_cell_size * 9  # Include label rows/columns
        return QSize(total_min_size, total_min_size)
    
    def sizeHint(self):
        """
        Provide a sensible default size hint.
        """
        # Default size of 540x540 pixels (9 * 60)
        return QSize(540, 540)

def create_square_board_container():
    """
    Create a container widget that maintains a perfect square aspect ratio.
    
    Returns:
        QWidget: A container that forces a square layout
    """
    container = QWidget()
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def resizeEvent(event):
        # Force square shape
        size = min(container.width(), container.height())
        container.setFixedSize(size, size)
    
    container.resizeEvent = resizeEvent
    return container