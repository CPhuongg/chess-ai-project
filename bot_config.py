"""
Lichess Bot Configuration and Setup Script
"""

import os
import sys
import requests

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = ['requests', 'chess', 'threading']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def validate_token(token):
    """Validate Lichess API token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get("https://lichess.org/api/account", headers=headers)
        
        if response.status_code == 200:
            account = response.json()
            print(f"Token valid! Account: {account.get('username')}")
            
            # Check if account is a bot account
            if account.get('title') == 'BOT':
                print("✓ Account is already a bot account")
                return True
            else:
                print("⚠ Warning: Account is not a bot account yet")
                print("You need to upgrade to bot account at: https://lichess.org/account/bot")
                return False
        else:
            print(f"Invalid token. Status code: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"Error validating token: {e}")
        return False

def create_config_file():
    """Create a configuration file for the bot"""
    config_template = '''# Lichess Bot Configuration
# Replace the values below with your actual settings

# Your Lichess API token (get from https://lichess.org/account/oauth/token)
API_TOKEN = "..."

# Path to opening book file (optional)
OPENING_BOOK_PATH = "resources/komodo.bin"

# Bot settings
BOT_NAME = "MyChessBot"

# Time management settings
MIN_THINK_TIME_MS = 100
MAX_THINK_TIME_MS = 30000
TIME_FRACTION = 40  # Divide remaining time by this number

# Challenge acceptance settings
ACCEPT_BULLET = True    # < 3 minutes
ACCEPT_BLITZ = True     # 3-8 minutes  
ACCEPT_RAPID = True     # 8-25 minutes
ACCEPT_CLASSICAL = True # > 25 minutes
ACCEPT_CORRESPONDENCE = False

# Variants to accept
ACCEPT_STANDARD = True
ACCEPT_CHESS960 = False
ACCEPT_VARIANTS = False
'''
    
    with open('bot_config.py', 'w') as f:
        f.write(config_template)
    
    print("Created bot_config.py file")
    print("Please edit it with your settings before running the bot")

def setup_bot():
    """Interactive bot setup"""
    print("Lichess Chess Bot Setup")
    print("=" * 30)
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Get API token
    token = input("Enter your Lichess API token: ").strip()
    if not token:
        print("No token provided")
        return False
    
    # Validate token
    if not validate_token(token):
        return False
    
    # Create config file
    create_config_file()
    
    print("\nSetup completed!")
    print("Next steps:")
    print("1. Edit bot_config.py with your preferences")
    print("2. Run the bot with: python lichess_bot.py")
    
    return True

def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        setup_bot()
    else:
        print("Usage:")
        print("  python bot_config.py setup  - Run interactive setup")
        print("  python lichess_bot.py       - Run the bot")

if __name__ == "__main__":
    main()