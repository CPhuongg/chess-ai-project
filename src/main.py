"""
main.py  –  Entry point.

Run:
    python -m src.main          (from project root)
    python src/main.py          (from project root)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from src.engine.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from src.ui.screens import MainMenuScreen, GameScreen, GameOverScreen
from src.board.board_manager import BoardManager


def main():
    pygame.init()
    pygame.display.set_caption("Chess AI  –  Minimax + Alpha-Beta + Fischer Clock")

    icon_path = os.path.join("assets","images","interface","icon.png")
    if os.path.isfile(icon_path):
        pygame.display.set_icon(pygame.image.load(icon_path))

    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock   = pygame.time.Clock()

    scene        = "menu"
    menu_screen  = MainMenuScreen(surface)
    game_screen  = None
    over_screen  = None
    last_config  = None

    while True:
        events = pygame.event.get()

        if scene == "menu":
            result = menu_screen.handle_events(events)
            menu_screen.update()
            menu_screen.draw()
            if result == "game":
                last_config = menu_screen.config
                game_screen = GameScreen(surface, last_config)
                over_screen = None
                scene = "game"

        elif scene == "game":
            result = game_screen.handle_events(events)
            game_screen.update()
            game_screen.draw()
            if result == "gameover":
                over_screen = GameOverScreen(surface,
                                             game_screen.board_mgr,
                                             game_screen.mode)
                scene = "gameover"
            elif result == "menu":
                menu_screen = MainMenuScreen(surface)
                game_screen = None
                scene = "menu"

        elif scene == "gameover":
            result = over_screen.handle_events(events)
            over_screen.update()
            over_screen.draw()
            if result == "game":
                game_screen = GameScreen(surface, last_config)
                over_screen = None
                scene = "game"
            elif result == "menu":
                menu_screen = MainMenuScreen(surface)
                game_screen = None
                over_screen = None
                scene = "menu"

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()