import requests
import json
import re
from datetime import datetime
import os
import glob
import markdown
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env file
MAX_LENGTH = 4096  # Telegram max character limit

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message, parse_mode=None):
        """
        Send a message to the specified chat

        Args:
            message (str): The message to send
            parse_mode (str): 'HTML' or 'Markdown' for formatting (optional)

        Returns:
            dict: Response from Telegram API
        """
        url = f"{self.base_url}/sendMessage"

        data = {
            'chat_id': self.chat_id,
            'text': message
        }

        if parse_mode:
            data['parse_mode'] = parse_mode

        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None

    # Add the method that was expected in the original script
    def send_notification(self, message, parse_mode=None):
        """
        Alias for send_message to maintain compatibility
        """
        return self.send_message(message, parse_mode)

    def test_connection(self):
        """
        Test if the bot token and setup are working
        """
        url = f"{self.base_url}/getMe"
        try:
            response = requests.get(url)
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                print(f"✅ Bot connected successfully!")
                print(f"   Bot Name: {bot_info.get('first_name', 'Unknown')}")
                print(f"   Username: @{bot_info.get('username', 'Unknown')}")
                return True
            else:
                print(f"❌ Bot connection failed: {result.get('description', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Error testing connection: {e}")
            return False

def load_portfolio_summary():
    """
    Load portfolio summary from the exports directory,
    remove <think> block, and limit to Telegram's 4096-character constraint.
    """
    today_str = datetime.now().strftime('%Y%m%d')
    search_path = f"exports/portfolio_analysis_{today_str}_*.txt"
    matching_files = glob.glob(search_path)
    latest_file = max(matching_files, key=os.path.getmtime) if matching_files else None
    file_path = os.path.abspath(latest_file) if latest_file else None

    print("Latest file path:", file_path)

    if not file_path or not os.path.exists(file_path):
        print(f"❌ Portfolio summary file not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            print("❌ Portfolio summary file is empty")
            return None

        # Remove the <think> block
        cleaned_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

        return cleaned_content
    except Exception as e:
        print(f"❌ Error reading portfolio summary: {e}")
        return 

def md_to_telegram(text):
    html = markdown.markdown(text)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()  # Or convert tags to Telegram-supported HTML

def main():
    """
    Main function to send portfolio notification
    """
    print("📊 Portfolio Telegram Notifier")
    print("=" * 50)

    # Configuration - Replace with your actual values
    BOT_TOKEN =  os.getenv('BOT_TOKEN')  # Replace with your bot token
    CHAT_ID =  os.getenv('CHAT_ID')      # Replace with your chat ID

    # Check if credentials are set
    if BOT_TOKEN == "YOUR_BOT_TOKEN" or CHAT_ID == "YOUR_CHAT_ID":
        print("❌ Please set your BOT_TOKEN and CHAT_ID in the script")
        print("   BOT_TOKEN: Get from @BotFather")
        print("   CHAT_ID: Use get_chat_id.py script or @RawDataBot")
        return

    # Initialize notifier
    notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID)

    # Test connection
    print("🔍 Testing bot connection...")
    if not notifier.test_connection():
        return

    # Load portfolio summary
    print("📖 Loading portfolio summary...")
    summary = load_portfolio_summary()
    
    clean_text = md_to_telegram((summary))
    if len(clean_text) > MAX_LENGTH: 
        clean_text = clean_text[:MAX_LENGTH]
    
    if not clean_text:
        return


    html_message = f"""
        {clean_text}
    """.strip()

    # Send notification
    print("📱 Sending notification to Telegram...")
    result = notifier.send_notification(html_message, parse_mode="HTML")

    if result and result.get('ok'):
        print("✅ Notification sent successfully!")
        message_id = result.get('result', {}).get('message_id', 'Unknown')
        print(f"   Message ID: {message_id}")
    else:
        print("❌ Failed to send notification")
        if result:
            print(f"   Error: {result.get('description', 'Unknown error')}")

if __name__ == "__main__":
    main()
