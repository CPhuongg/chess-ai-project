"""
Multiprocessing AI Worker - COMPLETE NON-BLOCKING SOLUTION
This completely separates AI computation from UI using separate processes.
"""

import multiprocessing as mp
import queue
import time
import traceback
from PyQt5.QtCore import QThread, pyqtSignal, QTimer

def ai_worker_process(board_fen, depth, time_ms, result_queue, cancel_event, 
                     white_time_ms=None, black_time_ms=None, white_inc_ms=None, black_inc_ms=None):
    """
    AI computation function that runs in a separate process with smart time management.
    """
    try:
        # Import bot only in worker process to avoid conflicts
        import sys
        import os
        
        # Add project root to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from bot import ChessBot
        from utils.config import Config
        
        # Create bot instance in worker process
        worker_bot = ChessBot(
            initial_fen=board_fen,
            opening_book_path="resources/komodo.bin"
        )
        
        # Check for cancellation
        if cancel_event.is_set():
            result_queue.put({"status": "cancelled", "move": None})
            return
        
        # Calculate optimal thinking time if time control parameters provided
        if all(param is not None for param in [white_time_ms, black_time_ms, white_inc_ms, black_inc_ms]):
            optimal_time = worker_bot.choose_think_time(
                white_time_ms, black_time_ms, white_inc_ms, black_inc_ms
            )
            # Use the smaller of requested time or optimal time
            actual_time_ms = min(time_ms, optimal_time)
            print(f"Smart time management: optimal={optimal_time}ms, using={actual_time_ms}ms")
        else:
            actual_time_ms = time_ms
            print(f"Fixed time management: using={actual_time_ms}ms")
        
        # Get best move with calculated time
        start_time = time.time()
        best_move = worker_bot.get_best_move(depth=depth, time_ms=actual_time_ms)
        elapsed_time = time.time() - start_time
        
        # Check for cancellation before returning result
        if cancel_event.is_set():
            result_queue.put({"status": "cancelled", "move": None})
        else:
            result_queue.put({
                "status": "success", 
                "move": best_move,
                "time_taken": elapsed_time,
                "time_allocated": actual_time_ms
            })
            
    except Exception as e:
        error_msg = f"AI Worker Error: {str(e)}\n{traceback.format_exc()}"
        result_queue.put({"status": "error", "error": error_msg})


class MultiprocessAIWorker(QThread):
    """
    Thread that manages a separate AI process with smart time management.
    """
    
    finished = pyqtSignal(str)  # Best move UCI
    error = pyqtSignal(str)     # Error message
    progress = pyqtSignal(int)  # Progress 0-100
    
    def __init__(self, board_fen, depth, time_ms=10000, 
                 white_time_ms=None, black_time_ms=None, white_inc_ms=None, black_inc_ms=None, parent=None):
        super().__init__(parent)
        self.board_fen = board_fen
        self.depth = depth
        self.time_ms = time_ms
        self.white_time_ms = white_time_ms
        self.black_time_ms = black_time_ms
        self.white_inc_ms = white_inc_ms
        self.black_inc_ms = black_inc_ms
        self.ai_process = None
        self.result_queue = None
        self.cancel_event = None
        self._cancelled = False
        
    def run(self):
        """Run AI computation in separate process with progress updates."""
        try:
            # Create multiprocessing objects
            self.result_queue = mp.Queue()
            self.cancel_event = mp.Event()
            
            self.progress.emit(10)
            
            # Start AI process with time management parameters
            self.ai_process = mp.Process(
                target=ai_worker_process,
                args=(self.board_fen, self.depth, self.time_ms, 
                      self.result_queue, self.cancel_event,
                      self.white_time_ms, self.black_time_ms, 
                      self.white_inc_ms, self.black_inc_ms)
            )
            self.ai_process.start()
            
            self.progress.emit(20)
            
            # Monitor process with progress updates
            start_time = time.time()
            timeout = (self.time_ms / 1000.0) + 10  # Add 10 second buffer
            
            while self.ai_process.is_alive():
                if self._cancelled:
                    self.cancel_event.set()
                    self.ai_process.terminate()
                    self.ai_process.join(timeout=2)
                    if self.ai_process.is_alive():
                        self.ai_process.kill()
                    self.finished.emit("")
                    return
                
                # Update progress based on elapsed time
                elapsed = time.time() - start_time
                progress = min(90, 20 + int((elapsed / timeout) * 70))
                self.progress.emit(progress)
                
                time.sleep(0.1)  # Check every 100ms
                
                # Timeout check
                if elapsed > timeout:
                    self.cancel_event.set()
                    self.ai_process.terminate()
                    self.ai_process.join(timeout=2)
                    if self.ai_process.is_alive():
                        self.ai_process.kill()
                    self.error.emit("AI computation timed out")
                    self.finished.emit("")
                    return
            
            # Get result from queue
            try:
                result = self.result_queue.get(timeout=1)
                self.progress.emit(100)
                
                if result["status"] == "success":
                    move = result.get("move", "")
                    time_taken = result.get("time_taken", 0)
                    time_allocated = result.get("time_allocated", self.time_ms)
                    print(f"AI found move: {move} (took {time_taken:.2f}s of {time_allocated/1000:.1f}s allocated)")
                    self.finished.emit(move or "")
                elif result["status"] == "error":
                    self.error.emit(result.get("error", "Unknown AI error"))
                    self.finished.emit("")
                else:  # cancelled
                    self.finished.emit("")
                    
            except queue.Empty:
                self.error.emit("AI process finished but no result received")
                self.finished.emit("")
                
        except Exception as e:
            error_msg = f"Multiprocess worker error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.error.emit(error_msg)
            self.finished.emit("")
        finally:
            self.cleanup()
    
    def cancel(self):
        """Cancel the AI computation."""
        self._cancelled = True
        if self.cancel_event:
            self.cancel_event.set()
    
    def cleanup(self):
        """Clean up process resources."""
        try:
            if self.ai_process and self.ai_process.is_alive():
                self.ai_process.terminate()
                self.ai_process.join(timeout=2)
                if self.ai_process.is_alive():
                    self.ai_process.kill()
        except Exception as e:
            print(f"Error cleaning up AI process: {e}")


class ResponsiveAIManager:
    """
    High-level manager for AI computation with smart time management.
    """
    
    def __init__(self, parent=None):
        self.parent = parent
        self.current_worker = None
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self._current_progress = 0
        
    def compute_move(self, board_fen, depth, time_ms, on_finished, on_error=None, on_progress=None,
                     white_time_ms=None, black_time_ms=None, white_inc_ms=None, black_inc_ms=None):
        """
        Start AI move computation with optional smart time management.
        
        Args:
            board_fen (str): Current board position
            depth (int): Search depth
            time_ms (int): Maximum time limit in milliseconds
            on_finished (callable): Callback when move is found
            on_error (callable): Callback for errors
            on_progress (callable): Callback for progress
            white_time_ms (int, optional): White's remaining time
            black_time_ms (int, optional): Black's remaining time  
            white_inc_ms (int, optional): White's time increment
            black_inc_ms (int, optional): Black's time increment
        """
        # Cancel any existing computation
        self.cancel_computation()
        
        # Create new worker with time management parameters
        self.current_worker = MultiprocessAIWorker(
            board_fen, depth, time_ms,
            white_time_ms, black_time_ms, white_inc_ms, black_inc_ms
        )
        
        # Connect callbacks
        self.current_worker.finished.connect(on_finished)
        if on_error:
            self.current_worker.error.connect(on_error)
        if on_progress:
            self.current_worker.progress.connect(on_progress)
        
        # Start computation
        self.current_worker.start()
        
        time_info = f"depth={depth}, max_time={time_ms}ms"
        if white_time_ms is not None:
            time_info += f", time_control=({white_time_ms}ms, {black_time_ms}ms, +{white_inc_ms}ms)"
        print(f"Started AI computation: {time_info}")
        
    def cancel_computation(self):
        """Cancel any ongoing AI computation."""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(1000)  # Wait up to 1 second
            if self.current_worker.isRunning():
                self.current_worker.terminate()
        self.current_worker = None
        
    def is_computing(self):
        """Check if AI is currently computing."""
        return self.current_worker and self.current_worker.isRunning()
        
    def _update_progress(self):
        """Internal progress update (for smooth progress bars if needed)."""
        pass
    
    

# Usage example for your UI:
"""
# In your UI class, create the manager:
self.ai_manager = ResponsiveAIManager(self)

# To get a move (replaces your current AI calls):
def start_ai_move(self):
    board_fen = self.board.fen()
    
    def on_move_ready(move_uci):
        # This runs on UI thread - no blocking!
        if move_uci:
            self.handle_ai_move_result(move_uci)
        else:
            self.handle_ai_error("No move found")
    
    def on_ai_error(error_msg):
        print(f"AI Error: {error_msg}")
        self.handle_ai_error(error_msg)
    
    def on_progress(percent):
        # Optional: update progress bar
        print(f"AI thinking: {percent}%")
    
    # Start computation - UI stays responsive!
    self.ai_manager.compute_move(
        board_fen=board_fen,
        depth=self.ai_depth,
        time_ms=10000,
        on_finished=on_move_ready,
        on_error=on_ai_error,
        on_progress=on_progress
    )

# To cancel (e.g., when user clicks cancel):
def cancel_ai_thinking(self):
    self.ai_manager.cancel_computation()
"""