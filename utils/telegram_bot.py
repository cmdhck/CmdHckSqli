import requests
import json
from kivy.clock import Clock

class TelegramBot:
    def __init__(self, app):
        self.app = app
    
    def test_connection(self):
        if not self.app.telegram_token or not self.app.telegram_chat_id:
            return False, "Token or Chat ID not set"
        
        url = f"https://api.telegram.org/bot{self.app.telegram_token}/getMe"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"API error: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def send_message(self, text):
        if not self.app.telegram_token or not self.app.telegram_chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{self.app.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.app.telegram_chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, data=payload)
            return response.status_code == 200
        except Exception as e:
            Clock.schedule_once(lambda dt: self.app.show_error(f"Telegram send failed: {str(e)}"))
            return False
    
    def send_document(self, file_path, caption=""):
        if not self.app.telegram_token or not self.app.telegram_chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{self.app.telegram_token}/sendDocument"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': self.app.telegram_chat_id, 'caption': caption}
                response = requests.post(url, files=files, data=data)
                return response.status_code == 200
        except Exception as e:
            Clock.schedule_once(lambda dt: self.app.show_error(f"Telegram file send failed: {str(e)}"))
            return False
