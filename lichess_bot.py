import requests
import json
import time
import threading
import random
from typing import Optional, Dict, Any, List
import chess
from bot import ChessBot
from tqdm import tqdm
import logging
import sys
from functools import wraps

class SafeFormatter(logging.Formatter):
    """Safe formatter that handles Unicode characters on Windows"""
    def format(self, record):
        msg = super().format(record)
        # Replace problematic Unicode characters for Windows console
        if sys.platform.startswith('win'):
            emoji_map = {
                '🔍': '[SEARCH]',
                '✅': '[SUCCESS]',
                '❌': '[ERROR]',
                '⚠️': '[WARNING]',
                '🎯': '[TARGET]',
                '🎮': '[GAME]',
                '🏁': '[FINISH]',
                '🤖': '[BOT]',
                '📊': '[STATS]',
                '🎨': '[COLOR]',
                '🏆': '[RESULT]',
                '⏱️': '[TIME]',
                '🔄': '[REFRESH]',
                '🚫': '[BLOCKED]',
                '⏳': '[WAIT]',
                '🧹': '[CLEANUP]',
                '🚀': '[START]',
                '🛑': '[STOP]',
                '🎧': '[LISTEN]',
                '📝': '[MOVE]',
                '🌐': '[CONNECT]',
                '👋': '[BYE]',
                '👤': '[USER]',
                '♟️': '[CHESS]',
                '🤔': '[THINK]',
                '🤝': '[DRAW]',
                '📈': '[UP]'
            }
            for emoji, replacement in emoji_map.items():
                msg = msg.replace(emoji, replacement)
        return msg

# Setup logging with safe formatter
def setup_logging():
    formatter = SafeFormatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler('lichess_bot.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

setup_logging()
logger = logging.getLogger(__name__)

class StrictRateLimiter:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 3.0  # 3 seconds between requests (conservative)
        self.lock = threading.Lock()
        self.blocked_until = 0  # Track when we can resume after 429
    
    def wait_if_needed(self):
        """Wait if needed to respect rate limits - ONLY ONE REQUEST AT A TIME"""
        with self.lock:
            current_time = time.time()
            
            # Check if we're still blocked from a 429 error
            if current_time < self.blocked_until:
                wait_time = self.blocked_until - current_time
                logger.warning(f"⏳ Still blocked from 429 error - waiting {wait_time:.1f}s more")
                time.sleep(wait_time)
            
            # Ensure minimum interval between requests
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.debug(f"⏱️ Rate limiting: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def handle_429_error(self):
        """Handle 429 error - wait 90 seconds as per requirement"""
        with self.lock:
            logger.error("🚫 HTTP 429 - Rate limited! Waiting 90 seconds")
            self.blocked_until = time.time() + 90  # Chờ 90 giây theo yêu cầu
            time.sleep(90)

def strict_rate_limited(func):
    """Decorator to add STRICT rate limiting to API calls"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'rate_limiter'):
            self.rate_limiter.wait_if_needed()
        
        try:
            result = func(self, *args, **kwargs)
            
            # Handle 429 rate limit - WAIT 90 SECONDS
            if hasattr(result, 'status_code') and result.status_code == 429:
                if hasattr(self, 'rate_limiter'):
                    self.rate_limiter.handle_429_error()
                # Retry ONCE after waiting
                self.rate_limiter.wait_if_needed()
                result = func(self, *args, **kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"API call error: {e}")
            raise
    
    return wrapper

class LichessBot:
    def __init__(self, api_token: str, opening_book_path: str = None):
        """
        Initialize Lichess Bot with STRICT rate limiting
        """
        self.api_token = api_token
        self.base_url = "https://lichess.org/api"
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.opening_book_path = opening_book_path
        
        # STRICT rate limiter - ONLY ONE REQUEST AT A TIME
        self.rate_limiter = StrictRateLimiter()
        
        # Simple game state tracking
        self.in_game = False
        self.current_game_id = None
        self.active_games = {}
        self.game_threads = {}
        self.is_challenging = False
        self.last_challenge_time = 0
        self.challenge_cooldown = 5  # 5 giây thay vì 180 giây
        self.running = True
        self.challenge_declined = False
        
        # Dynamic bot list
        self.available_bots = []
        self.tried_bots = set()
        self.last_bot_refresh = 0
        self.bot_refresh_interval = 10800  # 3 hours
        
        # Bot info
        self.bot_info = self.get_account_info()
        logger.info(f"✅ Bot initialized: {self.bot_info.get('username', 'Unknown')}")
        
        # Fetch initial bot list
        self.refresh_bot_list()
        
        # Start auto-challenger thread
        self.auto_challenge_thread = threading.Thread(target=self.auto_challenge_loop, daemon=True)
        self.auto_challenge_thread.start()
        
    @strict_rate_limited
    def get_account_info(self) -> Dict[str, Any]:
        """Get bot account information"""
        url = f"{self.base_url}/account"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get account info: {response.status_code}")
    
    def refresh_account_info(self):
        """Refresh account info to get updated ratings"""
        try:
            old_ratings = {}
            if self.bot_info.get('perfs'):
                for category in ['bullet', 'blitz', 'rapid', 'classical']:
                    if category in self.bot_info['perfs']:
                        old_ratings[category] = self.bot_info['perfs'][category].get('rating', 1500)
            
            self.bot_info = self.get_account_info()
            
            # Log rating changes
            new_ratings = {}
            if self.bot_info.get('perfs'):
                for category in ['bullet', 'blitz', 'rapid', 'classical']:
                    if category in self.bot_info['perfs']:
                        new_ratings[category] = self.bot_info['perfs'][category].get('rating', 1500)
                        if category in old_ratings and old_ratings[category] != new_ratings[category]:
                            change = new_ratings[category] - old_ratings[category]
                            logger.info(f"📈 {category.capitalize()} rating updated: {old_ratings[category]} → {new_ratings[category]} ({change:+d})")
            
            logger.info(f"🔄 Account info refreshed - ratings updated")
        except Exception as e:
            logger.error(f"❌ Error refreshing account info: {e}")
    
    def get_my_rating_for_time_control(self, category) -> int:
        """Get our rating for specific time control"""
        try:
            perfs = self.bot_info.get('perfs', {})
            
            # Get rating for this category
            if category in perfs:
                perf_data = perfs.get(category)
                return perf_data.get('rating', 1500)
            # Fallback
            return 1500
            
        except Exception as e:
            logger.error(f"Error getting rating for time control: {e}")
            return 1500
    
    def get_time_control_category(self, time_limit: int, increment: int = 0) -> str:
        """Get time control category name"""
        total_time = time_limit + increment * 40
        if total_time < 180:
            return 'bullet'
        elif total_time < 480:
            return 'blitz'
        elif total_time < 1500:
            return 'rapid'
        else:
            return 'classical'
    
    @strict_rate_limited
    def refresh_bot_list(self):
        """Fetch current list of online bots using /api/bot/online"""
        try:
            logger.info("🔄 Refreshing bot list...")
            
            url = f"{self.base_url}/bot/online"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to get online bots: {response.status_code}")
                return
            
            # Parse NDJSON response
            bots = []
            for line in response.text.strip().split('\n'):
                if line.strip():
                    try:
                        bot_data = json.loads(line)
                        if self.is_suitable_bot(bot_data):
                            bots.append(self.format_bot_data(bot_data))
                    except json.JSONDecodeError:
                        continue
            
            self.available_bots = bots
            self.tried_bots.clear()
            self.last_bot_refresh = time.time()
            
            logger.info(f"✅ Found {len(self.available_bots)} suitable bots")
            
        except Exception as e:
            logger.error(f"❌ Error refreshing bot list: {e}")
            self.available_bots = []
    
    def format_bot_data(self, bot_data: Dict) -> Dict:
        """Format bot data from API response"""
        perfs = bot_data.get('perfs', {})
        rating = 1500
        
        for perf_type in ['blitz', 'rapid', 'bullet', 'classical']:
            if perf_type in perfs and not perfs[perf_type].get('prov', False):
                rating = perfs[perf_type].get('rating', 1500)
                break
        
        return {
            'username': bot_data['username'],
            'id': bot_data['id'],
            'rating': rating,
            'online': True,
            'games': sum(perf.get('games', 0) for perf in perfs.values())
        }
    
    def is_suitable_bot(self, bot_data: Dict) -> bool:
        """Check if bot is suitable for challenging"""
        username = bot_data.get('username', '')
        
        # Skip our own bot
        my_username = self.bot_info.get('username', '').lower()
        if username.lower() == my_username:
            return False
        
        # Must be a bot
        if bot_data.get('title') != 'BOT':
            return False
        
        # Get rating for filtering
        perfs = bot_data.get('perfs', {})
        has_valid_rating = False
        
        for perf_type in ['blitz', 'rapid', 'bullet']:
            if perf_type in perfs:
                perf = perfs[perf_type]
                rating = perf.get('rating', 0)
                games = perf.get('games', 0)
                
                if 1000 <= rating <= 3000 and games > 10:
                    has_valid_rating = True
                    break
        
        return has_valid_rating
    
    def auto_challenge_loop(self):
        """Continuously challenge bots when idle"""
        logger.info("🎯 Auto-challenger started!")
        
        while self.running:
            try:
                # Refresh bot list periodically
                if time.time() - self.last_bot_refresh > self.bot_refresh_interval:
                    self.refresh_bot_list()
                
                # Only challenge if NOT in game
                if self.in_game:
                    logger.debug("🎮 Currently in game, waiting...")
                    time.sleep(15)
                    continue
                
                if self.is_challenging:
                    time.sleep(5)
                    continue
                
                # If challenge was declined, try immediately
                if self.challenge_declined:
                    self.challenge_declined = False
                    logger.info("🔄 Challenge declined, trying different bot...")
                    if self.available_bots:
                        self.challenge_random_bot()
                    continue
                
                # Normal cooldown logic - chỉ 5 giây
                time_since_last = time.time() - self.last_challenge_time
                if time_since_last < self.challenge_cooldown:
                    remaining = int(self.challenge_cooldown - time_since_last)
                    time.sleep(remaining)
                    continue
                
                # Try to challenge if idle
                if not self.in_game and not self.is_challenging:
                    if self.available_bots:
                        logger.info("🎯 Looking for opponent...")
                        self.challenge_random_bot()
                    else:
                        logger.info("❌ No suitable bots found, refreshing list...")
                        self.refresh_bot_list()
                        time.sleep(60)
                else:
                    time.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Auto-challenge error: {e}")
                time.sleep(30)
    
    def challenge_random_bot(self):
        """Challenge a random bot from the available list - ONLY ONE ATTEMPT"""
        if self.is_challenging or not self.running or not self.available_bots or self.in_game:
            if self.in_game:
                logger.debug("Cannot challenge - currently in game")
            return
            
        self.is_challenging = True
        
        try:
            # Time controls theo yêu cầu: 3+2, 15+1, 30+0
            time_controls = [
                {"time": 180, "increment": 2},   # Cờ chớp 3+2
                {"time": 900, "increment": 1},   # Cờ nhanh 15+1  
                {"time": 1800, "increment": 0},  # Cờ chậm 30+0
            ]
            
            selected_time_control = random.choice(time_controls)
            
            # Determine category for logging, rating
            category = self.get_time_control_category(
                selected_time_control["time"], 
                selected_time_control["increment"]
            )
            
            # Get our rating for this time control
            my_rating = self.get_my_rating_for_time_control(category)
            
            # Rating range: 80% - 120% theo yêu cầu
            max_rating = int(my_rating * 1.2)  # 120%
            min_rating = int(my_rating * 0.8)  # 80%
            
            logger.info(f"📊 My {category} rating: {my_rating}, Target range: {min_rating}-{max_rating}")
            
            # Get bots we haven't tried yet
            untried_bots = [bot for bot in self.available_bots if bot['username'] not in self.tried_bots]
            
            if not untried_bots:
                logger.info("🔄 Tried all bots, resetting...")
                self.tried_bots.clear()
                self.refresh_bot_list()
                untried_bots = self.available_bots.copy()
            
            if not untried_bots:
                logger.warning("❌ No bots available")
                return
            
            # Lọc bot theo rating range 80%-120%
            filtered_bots = [bot for bot in untried_bots 
                            if min_rating <= bot.get('rating', 1500) <= max_rating]
            
            if not filtered_bots:
                logger.warning(f"❌ No bots in range {min_rating}-{max_rating}")
                self.tried_bots.clear()
                return
            
            # Random shuffle những bot này
            random.shuffle(filtered_bots)
            
            # Challenge bot đầu tiên
            bot = filtered_bots[0]
            self.tried_bots.add(bot['username'])
            
            rating = bot.get('rating', 'N/A')
            rating_percent = (rating / my_rating * 100) if my_rating > 0 else 100
            logger.info(f"🎯 Challenging {bot['username']} (rating: {rating}, {rating_percent:.0f}% of my {category})")
            
            # Challenge with the pre-selected time control
            if self.try_challenge_bot_with_time_control(bot, selected_time_control):
                logger.info(f"✅ Successfully challenged {bot['username']} (rating: {rating})")
                return
            else:
                logger.warning("❌ Challenge attempt failed")
                        
        finally:
            self.is_challenging = False
            self.last_challenge_time = time.time()

    @strict_rate_limited
    def try_challenge_bot_with_time_control(self, bot: Dict, time_control: Dict) -> bool:
        """Try to challenge a specific bot with specific time control"""
        try:
            bot_name = bot['username']
            
            if bot_name.lower() == self.bot_info.get('username', '').lower():
                return False
            
            url = f"{self.base_url}/challenge/{bot_name}"
            data = {
                "rated": "true",
                "clock.limit": time_control["time"],
                "clock.increment": time_control["increment"],
                "color": "random",
                "variant": "standard"
            }
            
            response = requests.post(url, headers=self.headers, data=data)
            
            if response.status_code == 200:
                rating = bot.get('rating', 'N/A')
                category = self.get_time_control_category(time_control["time"], time_control["increment"])
                logger.info(f"✅ Challenge sent to {bot_name} ({rating}) - {time_control['time']}+{time_control['increment']} ({category})")
                return True
            elif response.status_code == 429:
                logger.error(f"🚫 Rate limited challenging {bot_name} - this should not happen with strict limiting!")
                return False
            else:
                logger.debug(f"Challenge failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception challenging {bot.get('username', 'unknown')}: {e}")
            return False
    
    def stream_events(self):
        """Stream incoming game events from Lichess"""
        url = f"{self.base_url}/stream/event"
        logger.info(f"🌐 Connected to Lichess events")
        
        while self.running:
            try:
                response = requests.get(url, headers=self.headers, stream=True, timeout=None)
                response.raise_for_status()
                
                for line in response.iter_lines(decode_unicode=True):
                    if line.strip() and self.running:
                        try:
                            event = json.loads(line)
                            self.handle_event(event)
                        except json.JSONDecodeError:
                            continue
                            
            except requests.exceptions.RequestException:
                if self.running:
                    logger.warning("🔄 Reconnecting...")
                    time.sleep(10)
                continue
            except KeyboardInterrupt:
                logger.info("\n👋 Bot stopped by user")
                self.running = False
                break
            except Exception as e:
                if self.running:
                    logger.error(f"Stream error: {e}")
                    time.sleep(10)
                continue
    
    def handle_event(self, event: Dict[str, Any]):
        """Handle different types of events from Lichess"""
        event_type = event.get('type')
        
        if event_type == 'gameStart':
            game_info = event['game']
            game_id = game_info['id']
            logger.info(f"🎮 Game started: {game_id}")
            
            # Set in_game = True
            self.in_game = True
            self.current_game_id = game_id
            self.is_challenging = False
            
            self.start_game_thread(game_id)
            
        elif event_type == 'gameFinish':
            game_info = event['game']
            game_id = game_info['id']
            logger.info(f"🏁 Game finished: {game_id}")
            
            # Log game result and ELO change
            self.log_game_result(game_id)
            
            # Refresh account info after game to get new rating
            self.refresh_account_info()
            
            # Set in_game = False
            self.in_game = False
            self.current_game_id = None
            
            self.cleanup_game(game_id)
            self.tried_bots.clear()
            
            # Đợi 5s sau đó thực hiện lại quá trình thách đấu
            self.last_challenge_time = time.time() - self.challenge_cooldown + 5
            
        elif event_type == 'challenge':
            challenge = event['challenge']
            challenger_name = challenge.get('challenger', {}).get('name', '')
            
            # Từ chối tất cả challenge theo yêu cầu
            logger.info(f"🚫 Auto-declining challenge from {challenger_name}")
            self.decline_challenge(challenge['id'])
            
        elif event_type == 'challengeDeclined':
            challenge_data = event.get('challenge', {})
            challenger = challenge_data.get('challenger', {}).get('name', 'Unknown')
            destUser = challenge_data.get('destUser', {}).get('name', 'Unknown')
            
            if challenger.lower() == self.bot_info.get('username', '').lower():
                logger.info(f"❌ Our challenge declined by {destUser}")
                if not self.in_game:
                    self.challenge_declined = True
        
        elif event_type == 'challengeCanceled':
            challenge_data = event.get('challenge', {})
            challenger = challenge_data.get('challenger', {}).get('name', 'Unknown')
            
            if challenger.lower() == self.bot_info.get('username', '').lower():
                logger.info(f"🚫 Our challenge was canceled")
                if not self.in_game:
                    self.challenge_declined = True
    
    @strict_rate_limited
    def log_game_result(self, game_id: str):
        """Log game result and ELO change"""
        try:
            time.sleep(5)  # Wait longer for Lichess to process
            
            url = f"{self.base_url}/game/export/{game_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                game_data = response.json()
                players = game_data.get('players', {})
                my_username = self.bot_info.get('username', '').lower()
                
                # Determine my color and get my data
                white_player = players.get('white', {})
                black_player = players.get('black', {})
                
                if white_player.get('user', {}).get('name', '').lower() == my_username:
                    my_data = white_player
                    opponent_data = black_player
                    my_color = 'white'
                else:
                    my_data = black_player
                    opponent_data = white_player
                    my_color = 'black'
                
                # Get game result
                winner = game_data.get('winner')
                status = game_data.get('status')
                
                if winner == my_color:
                    result = "🏆 WON"
                elif winner is None:
                    result = "🤝 DRAW"
                else:
                    result = "❌ LOST"
                
                # Get ELO change
                elo_change = my_data.get('ratingDiff', 0)
                opponent_name = opponent_data.get('user', {}).get('name', 'Unknown')
                opponent_elo = opponent_data.get('rating', 'N/A')
                
                # Get time control info
                clock = game_data.get('clock', {})
                time_limit = clock.get('initial', 0) // 1000  # Convert to seconds
                increment = clock.get('increment', 0) // 1000
                category = self.get_time_control_category(time_limit, increment)
                
                # Log the result
                logger.info(f"📊 GAME RESULT:")
                logger.info(f"   Result: {result}")
                logger.info(f"   Opponent: {opponent_name} ({opponent_elo})")
                logger.info(f"   Time Control: {time_limit}+{increment} ({category})")
                logger.info(f"   ELO Change: {elo_change:+d}")
                logger.info(f"   Status: {status}")
                
            else:
                logger.error(f"Failed to get game result: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting game result: {e}")
    
    def handle_challenge(self, challenge: Dict[str, Any]):
        """Handle incoming challenges"""
        challenge_id = challenge['id']
        challenger = challenge['challenger']['name']
        variant = challenge.get('variant', {}).get('name', 'standard')
        
        if variant.lower() == 'standard':
            self.accept_challenge(challenge_id)
            logger.info(f"✅ Accepted challenge from {challenger}")
        else:
            self.decline_challenge(challenge_id)
            logger.info(f"❌ Declined non-standard challenge from {challenger}")
    
    @strict_rate_limited
    def accept_challenge(self, challenge_id: str):
        """Accept a challenge"""
        url = f"{self.base_url}/challenge/{challenge_id}/accept"
        response = requests.post(url, headers=self.headers)
        return response
    
    @strict_rate_limited
    def decline_challenge(self, challenge_id: str):
        """Decline a challenge"""
        url = f"{self.base_url}/challenge/{challenge_id}/decline"
        response = requests.post(url, headers=self.headers)
        return response
    
    def start_game_thread(self, game_id: str):
        """Start a new thread to handle a game"""
        if game_id not in self.game_threads:
            thread = threading.Thread(target=self.play_game, args=(game_id,), daemon=True)
            self.game_threads[game_id] = thread
            thread.start()
    
    def play_game(self, game_id: str):
        """Play a single game"""
        chess_bot = ChessBot(opening_book_path=self.opening_book_path)
        self.active_games[game_id] = {
            'chess_bot': chess_bot,
            'my_color': None,
            'game_state': None
        }
        
        url = f"{self.base_url}/bot/game/stream/{game_id}"
        
        try:
            response = requests.get(url, headers=self.headers, stream=True, timeout=None)
            
            if response.status_code != 200:
                return
            
            for line in response.iter_lines(decode_unicode=True):
                if line.strip() and self.running:
                    try:
                        data = json.loads(line)
                        if not self.handle_game_event(game_id, data):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except Exception:
            pass
        finally:
            self.cleanup_game(game_id)
    
    def handle_game_event(self, game_id: str, data: Dict[str, Any]) -> bool:
        """Handle game events"""
        event_type = data.get('type')
        
        if event_type == 'gameFull':
            return self.handle_game_full(game_id, data)
        elif event_type == 'gameState':
            return self.handle_game_state(game_id, data)
        elif event_type == 'chatLine':
            self.handle_chat(game_id, data)
        
        return True
    
    def handle_game_full(self, game_id: str, data: Dict[str, Any]) -> bool:
        """Handle initial game state"""
        if game_id not in self.active_games:
            return False
            
        game_info = self.active_games[game_id]
        
        # Determine color
        white_player = data.get('white', {})
        black_player = data.get('black', {})
        my_username = self.bot_info.get('username', '').lower()
        
        if white_player.get('name', '').lower() == my_username:
            game_info['my_color'] = 'white'
            opponent = black_player
        elif black_player.get('name', '').lower() == my_username:
            game_info['my_color'] = 'black'
            opponent = white_player
        else:
            return False
        
        logger.info(f"♟️  Playing as {game_info['my_color']} vs {opponent.get('name')} (ELO: {opponent.get('rating')})")
        
        # Handle initial state
        initial_state = data.get('state', {})
        return self.handle_game_state(game_id, initial_state)
    
    def handle_game_state(self, game_id: str, state: Dict[str, Any]) -> bool:
        """Handle game state updates"""
        if game_id not in self.active_games:
            return False
            
        game_info = self.active_games[game_id]
        chess_bot = game_info['chess_bot']
        my_color = game_info['my_color']
        
        # Check if game is over
        status = state.get('status')
        if status in ['mate', 'resign', 'stalemate', 'timeout', 'draw', 'outoftime', 'cheat', 'noStart', 'aborted']:
            return False
        
        # Update position
        moves_str = state.get('moves', '')
        moves_list = moves_str.split() if moves_str else []
        
        try:
            chess_bot.set_position(moves=moves_list)
        except Exception:
            return False
        
        # Check if our turn
        move_count = len(moves_list)
        is_white_turn = move_count % 2 == 0
        is_my_turn = (my_color == 'white' and is_white_turn) or (my_color == 'black' and not is_white_turn)
        
        if is_my_turn and status == 'started':
            # Calculate thinking time
            wtime = state.get('wtime')
            btime = state.get('btime')
            winc = state.get('winc', 0)
            binc = state.get('binc', 0)
            
            if wtime is not None and btime is not None:
                think_time_ms = chess_bot.choose_think_time(wtime, btime, winc, binc)
            else:
                think_time_ms = 5000
            
            logger.info(f"🤔 Thinking for {think_time_ms/1000:.1f}s...")
            
            # Get move
            def on_move_chosen(move_uci):
                if move_uci:
                    try:
                        chess_bot.make_move(move_uci)
                    except Exception as e:
                        logger.error(f"Error making move on internal board: {e}")
                    
                    self.send_move(game_id, move_uci)
                    logger.info(f"♟️  Played: {move_uci}")
                else:
                    # Fallback
                    legal_moves = chess_bot.get_legal_moves()
                    if legal_moves:
                        fallback_move = legal_moves[0]
                        
                        try:
                            chess_bot.make_move(fallback_move)
                        except Exception as e:
                            logger.error(f"Error making fallback move: {e}")
                        
                        self.send_move(game_id, fallback_move)
                        logger.info(f"♟️  Played (fallback): {fallback_move}")
            
            chess_bot.on_move_chosen = on_move_chosen
            chess_bot.think_timed(think_time_ms)
        
        return True
    
    def handle_chat(self, game_id: str, data: Dict[str, Any]):
        """Handle chat messages"""
        text = data.get('text', '')
        
        if text.lower() in ['good luck', 'gl', 'glhf']:
            self.send_chat(game_id, "Good luck!")
        elif text.lower() in ['gg', 'good game']:
            self.send_chat(game_id, "Good game!")
    
    @strict_rate_limited
    def send_move(self, game_id: str, move_uci: str):
        """Send a move to Lichess"""
        url = f"{self.base_url}/bot/game/{game_id}/move/{move_uci}"
        response = requests.post(url, headers=self.headers)
        return response
    
    @strict_rate_limited
    def send_chat(self, game_id: str, message: str, room: str = 'player'):
        """Send a chat message"""
        url = f"{self.base_url}/bot/game/{game_id}/chat"
        data = {'room': room, 'text': message}
        response = requests.post(url, headers=self.headers, data=data)
        return response
    
    def cleanup_game(self, game_id: str):
        """Clean up resources for a finished game"""
        if game_id in self.active_games:
            chess_bot = self.active_games[game_id]['chess_bot']
            if hasattr(chess_bot, 'quit'):
                chess_bot.quit()
            del self.active_games[game_id]
        
        if game_id in self.game_threads:
            del self.game_threads[game_id]
        
        logger.info(f"🧹 Game {game_id} cleaned up")
    
    def run(self):
        """Start the bot"""
        logger.info("🚀 Lichess bot started!")
        logger.info(f"👤 Account: {self.bot_info.get('username')}")
        logger.info("🎯 Auto-challenger enabled with 90s wait on 429")
        
        try:
            self.stream_events()
        except KeyboardInterrupt:
            logger.info("\n👋 Bot stopped")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            self.running = False
        finally:
            self.cleanup_all_games()
    
    def cleanup_all_games(self):
        """Clean up all active games"""
        for game_id in list(self.active_games.keys()):
            self.cleanup_game(game_id)


def main():
    """Main function to run the bot"""
    # Set UTF-8 encoding for Windows
    if sys.platform.startswith('win'):
        import os
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    API_TOKEN = "..."  # Thay bằng token của bạn
    OPENING_BOOK_PATH = "resources/komodo.bin"
    
    # Test token
    print("🔍 Testing API token...")
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.get("https://lichess.org/api/account", headers=headers)
        if response.status_code != 200:
            print(f"❌ Invalid token: {response.status_code}")
            return
        
        account = response.json()
        print(f"✅ Token valid: {account.get('username')}")
        
        if not account.get('title') == 'BOT':
            print("⚠️  Warning: Not a BOT account")
        else:
            print("✅ BOT account verified!")
        
    except Exception as e:
        print(f"❌ Token error: {e}")
        return
    
    try:
        bot = LichessBot(API_TOKEN, OPENING_BOOK_PATH)
        bot.run()
    except Exception as e:
        print(f"❌ Failed to start: {e}")


if __name__ == "__main__":
    main()
