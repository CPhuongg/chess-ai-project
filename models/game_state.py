"""
Game state management for the chess application.
This module provides classes for tracking and managing chess game state.
"""

import chess
import datetime
from copy import deepcopy

class GameState:
    """
    Manages the state of a chess game including the board, move history, and game metadata.
    Provides a high-level API for interacting with the game state.
    """
    
    def __init__(self, initial_fen=None, mode="human_ai"):
        """
        Initialize a new game state.
        
        Args:
            initial_fen (str, optional): FEN string for starting position. Default is standard chess position.
            mode (str, optional): Game mode, either "human_ai" or "ai_ai". Default is "human_ai".
        """
        # Initialize the chess board
        self.board = chess.Board(initial_fen) if initial_fen else chess.Board()
        
        # Game configuration
        self.mode = mode
        self.turn = 'human' if self.mode == "human_ai" else 'ai1'
        self.ai_game_running = False
        self.ai_computation_active = False
        self.start_time = datetime.datetime.now()
    
    def make_move(self, move_uci):
        """
        Make a move on the board and update game state.
        
        Args:
            move_uci (str): Move in UCI format (e.g., "e2e4")
            
        Returns:
            bool: True if the move was successful, False otherwise
        """
        try:
            # Parse the move
            move = chess.Move.from_uci(move_uci)
            
            # Validate the move
            if move not in self.board.legal_moves:
                return False
            
            # Get move information before pushing
            from_square = chess.square_rank(move.from_square), chess.square_file(move.from_square)
            to_square = chess.square_rank(move.to_square), chess.square_file(move.to_square)
            piece = self.board.piece_at(move.from_square)
            is_capture = self.board.is_capture(move)
            
            # Store source and target square for highlighting
            self.last_move_from = (7 - from_square[0], from_square[1])
            self.last_move_to = (7 - to_square[0], to_square[1])
            
            # Check for special moves
            is_castling = piece and piece.piece_type == chess.KING and abs(move.from_square % 8 - move.to_square % 8) > 1
            is_en_passant = piece and piece.piece_type == chess.PAWN and abs(move.from_square % 8 - move.to_square % 8) == 1 and not self.board.piece_at(move.to_square)
            is_promotion = move.promotion is not None
            
            # Make the move
            self.board.push(move)
            
            # Add move to history
            self.move_history.append({
                'move': move,
                'piece': piece,
                'from_square': chess.square_name(move.from_square),
                'to_square': chess.square_name(move.to_square),
                'color': "White" if piece.color == chess.WHITE else "Black",
                'is_capture': is_capture,
                'is_check': self.board.is_check(),
                'is_castling': is_castling,
                'is_en_passant': is_en_passant,
                'is_promotion': is_promotion,
                'promotion_piece': move.promotion
            })
            
            # Update game state
            self._update_game_state()
            
            # Switch turns if the game is not over
            if not self.is_game_over:
                if self.mode == "human_ai":
                    self.turn = 'ai' if self.turn == 'human' else 'human'
                else:  # AI vs AI
                    self.turn = 'ai2' if self.turn == 'ai1' else 'ai1'
            
            return True
        
        except Exception as e:
            print(f"Error making move: {str(e)}")
            return False
    
    def undo_move(self):
        """
        Undo the last move and update game state.
        
        Returns:
            bool: True if a move was undone, False if there are no moves to undo
        """
        if not self.board.move_stack:
            return False
        
        # Pop the last move
        self.board.pop()
        
        # Also remove from our history
        if self.move_history:
            self.move_history.pop()
        
        # Update selected square and valid moves
        self.selected_square = None
        self.valid_moves = []
        self.castling_moves = []
        self.en_passant_moves = []
        
        # Update last move highlighting if there are still moves
        if self.board.move_stack:
            last_move = self.board.move_stack[-1]
            from_square = chess.square_rank(last_move.from_square), chess.square_file(last_move.from_square)
            to_square = chess.square_rank(last_move.to_square), chess.square_file(last_move.to_square)
            self.last_move_from = (7 - from_square[0], from_square[1])
            self.last_move_to = (7 - to_square[0], to_square[1])
        else:
            self.last_move_from = None
            self.last_move_to = None
        
        # Update game state
        self._update_game_state()
        
        # Update turn
        if self.mode == "human_ai":
            self.turn = 'human' if len(self.board.move_stack) % 2 == 0 else 'ai'
        else:  # AI vs AI
            self.turn = 'ai1' if len(self.board.move_stack) % 2 == 0 else 'ai2'
        
        return True
    
    def resign(self, color):
        """
        Resign the game for the specified color.
        
        Args:
            color (bool): Color resigning (chess.WHITE or chess.BLACK)
            
        Returns:
            str: Game result after resignation
        """
        if color == chess.WHITE:
            self.result = "0-1"
            self.winner = "Black"
        else:
            self.result = "1-0"
            self.winner = "White"
        
        self.is_game_over = True
        self.end_time = datetime.datetime.now()
        
        return self.result
    
    def find_valid_moves(self, square_name):
        """
        Find all valid moves for a piece on the given square.
        
        Args:
            square_name (str): Square name in algebraic notation (e.g., "e2")
            
        Returns:
            tuple: (regular_moves, castling_moves, en_passant_moves)
        """
        valid_moves = []
        castling_moves = []
        en_passant_moves = []
        
        # Parse the square
        square = chess.parse_square(square_name)
        
        # Get the piece on the square
        piece = self.board.piece_at(square)
        
        # Check if there's a piece and it's the current player's turn
        if not piece or piece.color != self.board.turn:
            return [], [], []
        
        # Find all legal moves from this square
        for move in self.board.legal_moves:
            if move.from_square == square:
                # Check for special moves
                if piece.piece_type == chess.KING and abs(move.from_square % 8 - move.to_square % 8) > 1:
                    # Castling - King moves more than one square horizontally
                    castling_moves.append(move)
                elif (piece.piece_type == chess.PAWN and 
                      abs(move.from_square % 8 - move.to_square % 8) == 1 and 
                      not self.board.piece_at(move.to_square)):
                    # En passant - Pawn moves diagonally but no piece at destination
                    en_passant_moves.append(move)
                else:
                    # Regular move
                    valid_moves.append(move)
        
        return valid_moves, castling_moves, en_passant_moves
    
    def _update_game_state(self):
        """Update the game state after a move."""
        # Check if game is over
        self.is_game_over = self.board.is_game_over()
        
        if self.is_game_over:
            self.end_time = datetime.datetime.now()
            
            # Determine result and winner
            if self.board.is_checkmate():
                self.result = "0-1" if self.board.turn == chess.WHITE else "1-0"
                self.winner = "Black" if self.board.turn == chess.WHITE else "White"
            elif self.board.is_stalemate():
                self.result = "1/2-1/2"
                self.winner = "Draw by stalemate"
            elif self.board.is_insufficient_material():
                self.result = "1/2-1/2"
                self.winner = "Draw by insufficient material"
            elif self.board.is_fifty_moves():
                self.result = "1/2-1/2"
                self.winner = "Draw by fifty-move rule"
            elif self.board.is_repetition():
                self.result = "1/2-1/2"
                self.winner = "Draw by repetition"
            else:
                self.result = "1/2-1/2"
                self.winner = "Draw"
    
    def get_fen(self):
        """Get the current board position as FEN."""
        return self.board.fen()
    
    def get_legal_moves(self):
        """Get all legal moves in the current position."""
        return [move.uci() for move in self.board.legal_moves]
    
    def is_check(self):
        """Check if the current player is in check."""
        return self.board.is_check()
    
    def to_dict(self):
        """
        Convert the game state to a dictionary for saving.
        
        Returns:
            dict: Game state as a dictionary
        """
        return {
            'fen': self.board.fen(),
            'mode': self.mode,
            'turn': self.turn,
            'last_move_from': self.last_move_from,
            'last_move_to': self.last_move_to,
            'move_history': [move.uci() for move in self.board.move_stack],
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'game_name': self.game_name,
            'game_notes': self.game_notes,
            'start_time': self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'end_time': self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            'is_game_over': self.is_game_over,
            'result': self.result,
            'winner': self.winner
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a game state from a dictionary.
        
        Args:
            data (dict): Game state dictionary
            
        Returns:
            GameState: New game state object
        """
        game_state = cls(initial_fen=data.get('fen'), mode=data.get('mode', 'human_ai'))
        game_state.turn = data.get('turn', 'human')
        game_state.last_move_from = data.get('last_move_from')
        game_state.last_move_to = data.get('last_move_to')
        game_state.game_name = data.get('game_name', 'Unnamed Game')
        game_state.game_notes = data.get('game_notes', '')
        
        # Rebuild the move stack
        # This will also update the board position to match the saved FEN
        move_history = data.get('move_history', [])
        temp_board = chess.Board()
        for move_uci in move_history:
            try:
                move = chess.Move.from_uci(move_uci)
                temp_board.push(move)
            except ValueError:
                print(f"Invalid move: {move_uci}")
        
        # Update game state
        game_state._update_game_state()
        
        return game_state = 'human' if mode == "human_ai" else 'ai1'
        
        # Game state tracking
        self.selected_square = None
        self.valid_moves = []
        self.castling_moves = []
        self.en_passant_moves = []
        self.last_move_from = None
        self.last_move_to = None
        self.is_game_over = False
        self.result = None
        self.winner = None
        
        # Move history for display and undo/redo
        self.move_history = []
        self.display_history = []  # For UI display (contains notation)
        
        # Game metadata
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.game_name = f"Game on {self.start_time.strftime('%Y-%m-%d %H:%M')}"
        self.game_notes = ""
        
        # AI state tracking
        self.ai_computation_active = False
        self.ai_depth = 3
        self.ai_game_running = False
    
    def reset(self):
        """Reset the game to initial state."""
        self.board.reset()
        self.selected_square = None
        self.valid_moves = []
        self.castling_moves = []
        self.en_passant_moves = []
        self.last_move_from = None
        self.last_move_to = None
        self.is_game_over = False
        self.result = None
        self.winner = None
        self.move_history = []
        self.display_history = []
        self.turn