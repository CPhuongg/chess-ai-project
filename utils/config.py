"""
Configuration management for the chess application.
This module provides a centralized way to manage application configuration.
"""

class Config:
    """Manages application configuration settings."""
    
    # Default application settings
    DEFAULT_AI_SEARCH_DEPTH = 3
    MAX_AI_SEARCH_DEPTH = 5
    MIN_AI_SEARCH_DEPTH = 1
    
    # UI Configuration
    DEFAULT_WINDOW_WIDTH = 1000
    DEFAULT_WINDOW_HEIGHT = 700
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    
    # Animation timing
    DEFAULT_ANIMATION_DURATION = 300  # ms
    THINKING_DOT_INTERVAL = 300  # ms
    
    # Time management settings
    DEFAULT_WHITE_INCREMENT_MS = 3000  # 3 seconds increment per move
    DEFAULT_BLACK_INCREMENT_MS = 3000  # 3 seconds increment per move
    MIN_THINKING_TIME_MS = 500         # Minimum time to think (0.5 seconds)
    MAX_THINKING_TIME_MS = 30000       # Maximum time to think (30 seconds)
    EMERGENCY_TIME_MS = 10000          # When to enter emergency mode (10 seconds)
    
    # Board colors
    LIGHT_SQUARE_COLOR = "#c1bfb0"
    DARK_SQUARE_COLOR = "#7a9bbe"
    SELECTED_SQUARE_COLOR = "#ffff99"
    LAST_MOVE_COLOR = "#ffe066"
    VALID_MOVE_COLOR = "#32CD32"
    CASTLING_MOVE_COLOR = "#FFA500"
    CHECK_COLOR = "#FF0000"
    EN_PASSANT_COLOR = "#9C27B0"  # Purple for en passant

    # Button colors
    START_BUTTON_COLOR = "#2ecc71"
    PAUSE_BUTTON_COLOR = "#f39c12"
    RESET_BUTTON_COLOR = "#3498db"
    SAVE_BUTTON_COLOR = "#16a085"
    HOME_BUTTON_COLOR = "#b57a33"
    RESIGN_BUTTON_COLOR = "#e74c3c"
    UNDO_BUTTON_COLOR = "#9b59b6"
    
    # Game modes
    MODE_HUMAN_AI = "human_ai"
    MODE_AI_AI = "ai_ai"
    