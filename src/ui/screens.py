"""
screens.py  –  MainMenuScreen, SettingsScreen, GameScreen, GameOverScreen.

Game modes
----------
  "hvai"  – Human (White) vs AI (Black)
  "aivh"  – AI (White) vs Human (Black)
  "avsa"  – AI vs AI (spectator)
  "hvh"   – Human vs Human (local)
"""

import sys, os, threading, time, datetime
import chess, pygame

from src.board.board_manager import BoardManager
from src.engine.minimax      import ChessEngine
from src.engine.constants    import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BOARD_SIZE, SQUARE_SIZE,
    BOARD_OFFSET_X, BOARD_OFFSET_Y, FPS,
    C_BG, C_PANEL, C_CARD, C_ACCENT, C_WHITE, C_GREY,
    C_GREEN, C_RED, C_YELLOW,
    DIFFICULTY, TIME_CONTROLS,
)
from src.ui.renderer   import Renderer
from src.ui.animation  import AnimationManager
from src.ui.components import (
    Button, ToggleButton, EvalBar, ClockDisplay,
    CapturedDisplay, MoveHistoryPanel, PromotionDialog,
)

# ── Panel geometry ─────────────────────────────────────────
PNL_X  = BOARD_OFFSET_X + BOARD_SIZE + 28
PNL_W  = WINDOW_WIDTH - PNL_X - 14
PNL_Y  = BOARD_OFFSET_Y


def _fonts():
    try:
        sm  = pygame.font.Font(None, 17)
        reg = pygame.font.Font(None, 20)
        med = pygame.font.Font(None, 26)
        big = pygame.font.Font(None, 44)
        xl  = pygame.font.Font(None, 60)
    except Exception:
        sm  = pygame.font.SysFont("arial", 13)
        reg = pygame.font.SysFont("arial", 15)
        med = pygame.font.SysFont("arial", 20)
        big = pygame.font.SysFont("arial", 32, bold=True)
        xl  = pygame.font.SysFont("arial", 46, bold=True)
    return sm, reg, med, big, xl


# ══════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════
class MainMenuScreen:
    def __init__(self, surf):
        self.surf = surf
        self.sm, self.reg, self.med, self.big, self.xl = _fonts()
        cx = WINDOW_WIDTH // 2

        # Mode buttons
        self._modes = [
            ("hvai", "Human  vs  AI"),
            ("aivh", "AI  vs  Human"),
            ("avsa", "AI  vs  AI  (Watch)"),
            ("hvh",  "Human  vs  Human"),
        ]
        self._mode_btns = [
            ToggleButton(cx-160, 220+i*58, 320, 44, label, self.med)
            for i, (_, label) in enumerate(self._modes)
        ]
        self._mode_btns[0].selected = True
        self._sel_mode = "hvai"

        # Difficulty
        self._diffs  = list(DIFFICULTY.keys())
        self._diff_btns = [
            ToggleButton(cx - 200 + i*102, 470, 96, 36, d, self.reg)
            for i, d in enumerate(self._diffs)
        ]
        self._diff_btns[1].selected = True   # Medium default
        self._sel_diff = "Medium"

        # Time control
        self._tcs    = list(TIME_CONTROLS.keys())
        self._tc_btns = [
            ToggleButton(cx - 260 + i*107, 550, 102, 34, tc, self.sm)
            for i, tc in enumerate(self._tcs)
        ]
        self._tc_btns[4].selected = True   # No limit default
        self._sel_tc  = list(TIME_CONTROLS.keys())[4]

        self.btn_start = Button(cx-130, 622, 260, 50, "Start Game", self.med,
                                color=(40,120,60), hover=(50,150,75), radius=12)
        self.btn_quit  = Button(cx-80,  688, 160, 38, "Quit", self.reg,
                                color=(80,30,30), hover=(110,40,40), radius=8)
        self._next = None

    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()

            for i, btn in enumerate(self._mode_btns):
                if btn.handle_event(ev):
                    for b in self._mode_btns: b.selected = False
                    btn.selected = True
                    self._sel_mode = self._modes[i][0]

            for i, btn in enumerate(self._diff_btns):
                if btn.handle_event(ev):
                    for b in self._diff_btns: b.selected = False
                    btn.selected = True
                    self._sel_diff = self._diffs[i]

            for i, btn in enumerate(self._tc_btns):
                if btn.handle_event(ev):
                    for b in self._tc_btns: b.selected = False
                    btn.selected = True
                    self._sel_tc = self._tcs[i]

            if self.btn_start.handle_event(ev): self._next = "game"
            if self.btn_quit.handle_event(ev):  pygame.quit(); sys.exit()

        nxt = self._next; self._next = None
        return nxt

    def update(self): pass

    def draw(self):
        self.surf.fill(C_BG)
        cx = WINDOW_WIDTH // 2

        # Title
        # Title: render chess king as separate surface using unicode font if available
        title_text = "Chess AI"
        t = self.xl.render(title_text, True, C_ACCENT)
        # Try to draw a chess piece icon before the title
        piece_drawn = False
        """
        try:
            uf = pygame.font.SysFont("segoeuisymbol,seguisym,dejavusans,freesans", 50)
            piece = uf.render("K", True, C_ACCENT)
            if piece.get_width() > 5:
                total_w = piece.get_width() + 12 + t.get_width()
                px = cx - total_w // 2
                self.surf.blit(piece, piece.get_rect(y=62, x=px))
                self.surf.blit(t, t.get_rect(y=60, x=px + piece.get_width() + 12))
                #piece_drawn = True
        except Exception:
            pass
        """
        if not piece_drawn:
            self.surf.blit(t, t.get_rect(centerx=cx, y=60))
        
        #sub = self.reg.render("Minimax  |  Alpha-Beta  |  Piece-Square Tables  |  Fischer Clock", True, C_GREY)
        #self.surf.blit(sub, sub.get_rect(centerx=cx, y=120))

        # Section labels
        for label, y in [("Game Mode", 190), ("Difficulty", 445), ("Time Control", 525)]:
            lbl = self.reg.render(label, True, C_GREY)
            self.surf.blit(lbl, (cx - lbl.get_width()//2, y))
            pygame.draw.line(self.surf, (55,55,65),
                             (cx-150, y+16), (cx+150, y+16))

        for b in self._mode_btns: b.draw(self.surf)
        for b in self._diff_btns: b.draw(self.surf)
        for b in self._tc_btns:   b.draw(self.surf)
        self.btn_start.draw(self.surf)
        self.btn_quit.draw(self.surf)

    @property
    def config(self):
        base, inc = TIME_CONTROLS[self._sel_tc]
        return {
            "mode":       self._sel_mode,
            "difficulty": self._sel_diff,
            "base_sec":   base,
            "inc_sec":    inc,
        }


# ══════════════════════════════════════════════════════════
# GAME SCREEN
# ══════════════════════════════════════════════════════════
class GameScreen:
    """
    Handles all four game modes.
    In AI-vs-AI, both sides are computed; the game advances
    automatically after a short display delay.
    """

    _AI_VS_AI_DELAY = 0.5   # seconds between AI moves in spectator mode

    def __init__(self, surf, config: dict):
        self.surf   = surf
        self.mode   = config["mode"]           # hvai / aivh / avsa / hvh
        self.diff   = config["difficulty"]
        base        = config["base_sec"]
        inc         = config["inc_sec"]

        self.sm, self.reg, self.med, self.big, self.xl = _fonts()

        self.board_mgr = BoardManager(base, inc)
        self._set_names()

        # Engines
        self._engine_black = ChessEngine(self.diff) if self.mode in ("hvai","avsa") else None
        self._engine_white = ChessEngine(self.diff) if self.mode in ("aivh","avsa") else None

        self.renderer   = Renderer(surf, self.reg, self.med)
        # EvalBar sits in the 28px gap between board right edge and side panel
        EVAL_X = BOARD_OFFSET_X + BOARD_SIZE + 4
        self.eval_bar   = EvalBar(EVAL_X, PNL_Y, BOARD_SIZE, self.sm, width=20)
        self.cap_disp   = CapturedDisplay(PNL_X+8, PNL_Y+6, self.sm)
        self.move_panel = MoveHistoryPanel(PNL_X+4, PNL_Y+50, PNL_W-8, 285, self.reg)

        # Clocks
        clk_w = (PNL_W-8)//2 - 2
        self.clock_white = ClockDisplay(PNL_X+4, PNL_Y+352, clk_w, 62, self.med, self.sm,
                                        C_WHITE, "White")
        self.clock_black = ClockDisplay(PNL_X+clk_w+8, PNL_Y+352, clk_w, 62, self.med, self.sm,
                                        C_WHITE, "Black")

        # Sidebar buttons
        by = PNL_Y + 428
        hw = (PNL_W-12)//2
        self.btn_undo = Button(PNL_X+4,      by,    hw,   34, "Undo",     self.reg)
        self.btn_flip = Button(PNL_X+hw+8,   by,    hw,   34, "Flip",     self.reg)
        self.btn_save = Button(PNL_X+4,      by+44, PNL_W-8,34,"Save PGN", self.reg)
        self.btn_menu = Button(PNL_X+4,      by+88, PNL_W-8,34,"Main Menu",self.reg,
                               color=(70,30,30), hover=(100,40,40))

        # Interaction state
        self.selected_sq  = None
        self.legal_moves  = []
        self.flipped      = (self.mode == "aivh")
        self.dragging     = False
        self.drag_piece   = None
        self.drag_from    = None

        # Promotion
        self.promo_dialog = PromotionDialog(
            BOARD_OFFSET_X + BOARD_SIZE//2,
            BOARD_OFFSET_Y + BOARD_SIZE//2,
            self.big)
        self._pending_promo: chess.Move | None = None

        # Animation
        self.anim = AnimationManager()

        # AI threading
        self._ai_busy  = False
        self._ai_move  = None
        self._ai_score = 0
        self._ai_info  = {}
        self._ai_timer = 0.0   # for AI-vs-AI pacing

        self._next = None
        self._save_msg = ""
        self._save_msg_t = 0.0

        # Trigger AI if it moves first
        self._maybe_trigger_ai()

    def _set_names(self):
        MODE_NAMES = {
            "hvai": ("Player", "AI"),
            "aivh": ("AI", "Player"),
            "avsa": ("AI (White)", "AI (Black)"),
            "hvh":  ("Player 1", "Player 2"),
        }
        w, b = MODE_NAMES.get(self.mode, ("White","Black"))
        self.board_mgr.white_name = w
        self.board_mgr.black_name = b

    # ── AI helpers ────────────────────────────────────────
    def _is_ai_turn(self) -> bool:
        turn = self.board_mgr.turn
        if self.mode == "avsa": return True
        if self.mode == "hvai": return turn == chess.BLACK
        if self.mode == "aivh": return turn == chess.WHITE
        return False

    def _engine_for_turn(self):
        turn = self.board_mgr.turn
        if turn == chess.WHITE: return self._engine_white
        return self._engine_black

    def _maybe_trigger_ai(self):
        if self.board_mgr.is_game_over: return
        if self._ai_busy: return
        if not self._is_ai_turn(): return
        eng = self._engine_for_turn()
        if eng is None: return
        self._ai_busy = True
        board_copy = self.board_mgr.board.copy()
        def _run():
            move, score, info = eng.best_move(board_copy)
            self._ai_move  = move
            self._ai_score = score
            self._ai_info  = info
            self._ai_busy  = False
        threading.Thread(target=_run, daemon=True).start()

    def _apply_ai_move(self):
        if self._ai_move is None or self._ai_busy: return
        move = self._ai_move
        self._ai_move = None
        if move and not self.board_mgr.is_game_over:
            board        = self.board_mgr.board
            moving_piece = board.piece_at(move.from_square)
            cap_sq       = move.to_square
            if board.is_en_passant(move):
                ep_rank = 4 if board.turn == chess.WHITE else 3
                cap_sq  = chess.square(chess.square_file(move.to_square), ep_rank)
            captured = board.piece_at(cap_sq)
            self.board_mgr.push_move(move)
            if moving_piece:
                self.anim.trigger_ai_move(move, moving_piece, captured,
                                          flipped=self.flipped)
            self.eval_bar.update(self._ai_score)
            if self.board_mgr.is_game_over:
                self._next = "gameover"
            else:
                self._maybe_trigger_ai()

    # ── Board click / drag ────────────────────────────────
    def _is_human_turn(self) -> bool:
        if self.mode == "avsa": return False
        if self.mode == "hvh":  return True
        turn = self.board_mgr.turn
        if self.mode == "hvai": return turn == chess.WHITE
        if self.mode == "aivh": return turn == chess.BLACK
        return False

    def _board_click(self, pos):
        if not self._is_human_turn(): return
        if self._ai_busy: return
        sq = Renderer.px_to_sq(*pos, flipped=self.flipped)
        if sq is None:
            self.selected_sq = None; self.legal_moves = []; return

        board = self.board_mgr.board

        # Try to complete a move
        if self.selected_sq is not None:
            for move in self.legal_moves:
                if move.to_square == sq:
                    if move.promotion:
                        # Need to pick piece
                        self._pending_promo = chess.Move(move.from_square, sq)
                        self.promo_dialog.show(board.turn)
                        return
                    self._push_human(move)
                    return

        # Select a piece
        piece = board.piece_at(sq)
        if piece and piece.color == board.turn:
            self.selected_sq = sq
            self.legal_moves = self.board_mgr.legal_moves_from(sq)
        else:
            self.selected_sq = None; self.legal_moves = []

    def _push_human(self, move: chess.Move):
        # Grab piece info BEFORE pushing
        board        = self.board_mgr.board
        moving_piece = board.piece_at(move.from_square)
        cap_sq       = move.to_square
        if board.is_en_passant(move):
            ep_rank  = 4 if board.turn == chess.WHITE else 3
            cap_sq   = chess.square(chess.square_file(move.to_square), ep_rank)
        captured     = board.piece_at(cap_sq)

        ok = self.board_mgr.push_move(move)
        self.selected_sq = None; self.legal_moves = []
        self.anim.drag.stop()
        if ok and moving_piece:
            self.anim.trigger_move(move, moving_piece, captured,
                                   flipped=self.flipped)
            self.eval_bar.update(self._ai_score)
            if self.board_mgr.is_game_over:
                self._next = "gameover"
            else:
                self._maybe_trigger_ai()

    # ── Save PGN ──────────────────────────────────────────
    def _save_pgn(self):
        os.makedirs("data", exist_ok=True)
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"data/game_{ts}.pgn"
        self.board_mgr.save_pgn(path)
        self._save_msg   = f"Saved: {path}"
        self._save_msg_t = time.perf_counter()

    # ── Event handling ────────────────────────────────────
    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()

            # Promotion dialog first
            pt = self.promo_dialog.handle_event(ev)
            if pt is not None and self._pending_promo is not None:
                move = chess.Move(self._pending_promo.from_square,
                                  self._pending_promo.to_square,
                                  promotion=pt)
                self._pending_promo = None
                self._push_human(move)
                continue

            if self.btn_undo.handle_event(ev):
                self.board_mgr.undo_move()
                if self.mode in ("hvai","aivh"):
                    self.board_mgr.undo_move()
                self.selected_sq = None; self.legal_moves = []
                self._ai_move = None
            if self.btn_flip.handle_event(ev):
                self.flipped = not self.flipped
                self.anim.update_flipped(self.flipped)
            if self.btn_save.handle_event(ev): self._save_pgn()
            if self.btn_menu.handle_event(ev): self._next = "menu"

            # Mouse wheel for move history scroll
            self.move_panel.handle_event(ev)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                bx, by = BOARD_OFFSET_X, BOARD_OFFSET_Y
                if bx <= ev.pos[0] < bx+BOARD_SIZE and by <= ev.pos[1] < by+BOARD_SIZE:
                    self._board_click(ev.pos)
                    # Start drag if a piece got selected
                    if self.selected_sq is not None and self._is_human_turn():
                        piece = self.board_mgr.board.piece_at(self.selected_sq)
                        if piece:
                            self.anim.drag.start(piece, self.selected_sq, ev.pos)

            if ev.type == pygame.MOUSEMOTION:
                if self.anim.drag.active:
                    self.anim.drag.move(ev.pos)

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if self.anim.drag.active:
                    bx, by = BOARD_OFFSET_X, BOARD_OFFSET_Y
                    if bx <= ev.pos[0] < bx+BOARD_SIZE and by <= ev.pos[1] < by+BOARD_SIZE:
                        drop_sq = self.renderer.px_to_sq(*ev.pos, flipped=self.flipped)
                        if drop_sq is not None and self.selected_sq is not None:
                            for move in self.legal_moves:
                                if move.to_square == drop_sq:
                                    if move.promotion and move.promotion != chess.QUEEN:
                                        continue
                                    self._push_human(move)
                                    break
                            else:
                                self.anim.drag.stop()
                    else:
                        self.anim.drag.stop()
                        self.selected_sq = None
                        self.legal_moves = []

        # Clock flag check
        mgr = self.board_mgr
        if not mgr.is_game_over:
            if mgr.clock.is_flagged(chess.WHITE) or mgr.clock.is_flagged(chess.BLACK):
                self._next = "gameover"

        nxt = self._next; self._next = None
        return nxt

    def update(self):
        # Apply ready AI move (with pacing for AI-vs-AI)
        if not self._ai_busy and self._ai_move is not None:
            if self.mode == "avsa":
                if time.perf_counter() - self._ai_timer >= self._AI_VS_AI_DELAY:
                    self._apply_ai_move()
                    self._ai_timer = time.perf_counter()
            else:
                self._apply_ai_move()

    # ── Draw ─────────────────────────────────────────────
    def draw(self):
        self.renderer.fill_bg()

        mgr = self.board_mgr
        self.renderer.draw_board(
            mgr.board,
            selected_sq = self.selected_sq,
            legal_moves = self.legal_moves,
            last_move   = mgr.last_move,
            flipped     = self.flipped,
        )
        # Determine which squares to skip (being animated or dragged)
        skip_sqs = set()
        if self.anim.slide_src is not None:  skip_sqs.add(self.anim.slide_src)
        if self.anim.slide_dst is not None:  skip_sqs.add(self.anim.slide_dst)
        if self.anim.drag.active and self.anim.drag.from_sq is not None:
            skip_sqs.add(self.anim.drag.from_sq)

        # Draw static pieces (skip animated ones)
        for sq in chess.SQUARES:
            if sq in skip_sqs: continue
            piece = mgr.board.piece_at(sq)
            if piece:
                self.renderer._draw_one_piece(
                    piece, sq, self.flipped, self.renderer._piece_font())

        # Capture pop (behind slide)
        self.anim.draw_captures(self.surf, self.renderer)

        # Sliding piece
        self.anim.draw_slides(self.surf, self.renderer)

        # Dragged piece (topmost layer)
        self.anim.draw_drag(self.surf, self.renderer)

        self.renderer.draw_coords(self.flipped)
        self.renderer.draw_border()

        # Side panel
        self.renderer.draw_panel_bg(PNL_X-4, PNL_Y-4, PNL_W+8, BOARD_SIZE+8)

        # Eval bar
        self.eval_bar.draw(self.surf)

        # Captured pieces
        self.cap_disp.draw(self.surf, mgr.captured_pieces)

        # Move history
        self.move_panel.draw(self.surf, mgr.move_history_san())

        # Clocks
        clk = mgr.clock
        self.clock_white.time_str = clk.fmt(chess.WHITE)
        self.clock_white.active   = (mgr.turn == chess.WHITE and not mgr.is_game_over)
        self.clock_white.flagged  = clk.is_flagged(chess.WHITE)
        self.clock_black.time_str = clk.fmt(chess.BLACK)
        self.clock_black.active   = (mgr.turn == chess.BLACK and not mgr.is_game_over)
        self.clock_black.flagged  = clk.is_flagged(chess.BLACK)
        self.clock_white.draw(self.surf)
        self.clock_black.draw(self.surf)

        # Buttons
        self.btn_undo.draw(self.surf)
        self.btn_flip.draw(self.surf)
        self.btn_save.draw(self.surf)
        self.btn_menu.draw(self.surf)

        # AI thinking indicator
        if self._ai_busy:
            eng = self._engine_for_turn()
            diff = eng.difficulty if eng else "?"
            side = "White" if mgr.turn == chess.WHITE else "Black"
            txt = f"{side} AI ({diff}) thinking..."
            lbl = self.reg.render(txt, True, C_YELLOW)
            self.surf.blit(lbl, (BOARD_OFFSET_X,
                                 BOARD_OFFSET_Y + BOARD_SIZE + 6))

        # Turn indicator (human modes)
        elif not mgr.is_game_over and self._is_human_turn():
            turn_str = "Your turn — " + ("White" if mgr.turn==chess.WHITE else "Black")
            lbl = self.reg.render(turn_str, True, C_GREY)
            self.surf.blit(lbl,(BOARD_OFFSET_X, BOARD_OFFSET_Y+BOARD_SIZE+6))

        # Check warning
        if mgr.is_in_check() and not mgr.is_game_over:
            lbl = self.med.render("CHECK!", True, C_RED)
            self.surf.blit(lbl,(BOARD_OFFSET_X + BOARD_SIZE//2 - lbl.get_width()//2,
                                BOARD_OFFSET_Y - 28))

        # Difficulty badge
        diff_lbl = self.sm.render(f"AI: {self.diff}", True, C_GREY)
        self.surf.blit(diff_lbl,(PNL_X+4, PNL_Y-20))

        # Save message
        if self._save_msg and time.perf_counter() - self._save_msg_t < 3.0:
            lbl = self.sm.render(self._save_msg, True, C_GREEN)
            self.surf.blit(lbl,(BOARD_OFFSET_X, BOARD_OFFSET_Y+BOARD_SIZE+24))

        # Promotion dialog (on top of everything)
        self.promo_dialog.draw(self.surf)


# ══════════════════════════════════════════════════════════
# GAME OVER SCREEN
# ══════════════════════════════════════════════════════════
class GameOverScreen:
    def __init__(self, surf, board_mgr: BoardManager, game_mode: str):
        self.surf      = surf
        self.board_mgr = board_mgr
        self.mode      = game_mode
        self.sm, self.reg, self.med, self.big, self.xl = _fonts()

        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        self.btn_new  = Button(cx-140, cy+80, 130, 46, "New Game", self.med,
                               color=(40,100,50), hover=(50,130,65))
        self.btn_menu = Button(cx+10,  cy+80, 130, 46, "Menu",   self.med)
        self.btn_save = Button(cx-65,  cy+140, 130, 38, "Save PGN", self.reg)

        self._next       = None
        self._saved      = False

    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if self.btn_new.handle_event(ev):  self._next = "game"
            if self.btn_menu.handle_event(ev): self._next = "menu"
            if self.btn_save.handle_event(ev):
                os.makedirs("data", exist_ok=True)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self.board_mgr.save_pgn(f"data/game_{ts}.pgn")
                self._saved = True

        nxt = self._next; self._next = None
        return nxt

    def update(self): pass

    def draw(self):
        self.surf.fill(C_BG)
        cx = WINDOW_WIDTH//2; cy = WINDOW_HEIGHT//2

        reason = self.board_mgr.game_over_reason()
        result = self.board_mgr.result_with_flag()

        RESULT_COLOR = {
            "1-0": C_WHITE,  "0-1": C_GREY,  "1/2-1/2": C_YELLOW, "*": C_GREY,
        }
        # Decorative line
        pygame.draw.line(self.surf, C_ACCENT,
                         (cx-200, cy-120), (cx+200, cy-120), 2)

        title = self.xl.render("Game Over", True, C_ACCENT)
        self.surf.blit(title, title.get_rect(centerx=cx, y=cy-110))

        rlbl = self.big.render(result, True, RESULT_COLOR.get(result, C_WHITE))
        self.surf.blit(rlbl, rlbl.get_rect(centerx=cx, y=cy-50))

        rlbl2 = self.med.render(reason, True, C_WHITE)
        self.surf.blit(rlbl2, rlbl2.get_rect(centerx=cx, y=cy))

        # Move count
        n = len(self.board_mgr.move_history)
        mlbl = self.reg.render(f"{(n+1)//2} moves played", True, C_GREY)
        self.surf.blit(mlbl, mlbl.get_rect(centerx=cx, y=cy+36))

        pygame.draw.line(self.surf, (55,55,65),
                         (cx-200, cy+68), (cx+200, cy+68))

        self.btn_new.draw(self.surf)
        self.btn_menu.draw(self.surf)
        self.btn_save.draw(self.surf)

        if self._saved:
            lbl = self.reg.render("PGN saved to /data/", True, C_GREEN)
            self.surf.blit(lbl, lbl.get_rect(centerx=cx, y=cy+188))