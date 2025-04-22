import os
import json
import threading
from datetime import datetime
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.button import MDRectangleFlatButton, MDFillRoundFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.textfield import MDTextField
from kivymd.uix.snackbar import Snackbar
from utils.telegram_bot import TelegramBot
from utils.sqlmap_wrapper import SQLMapWrapper

# Set window background color
Window.clearcolor = get_color_from_hex('#121212')

# Load KV language string
KV = '''
#:import get_color_from_hex kivy.utils.get_color_from_hex

<CustomTextField>:
    hint_text_color: app.theme_cls.primary_color
    foreground_color: get_color_from_hex('#00ff99') if self.focus else get_color_from_hex('#aaaaaa')
    background_color: get_color_from_hex('#1e1e1e')
    line_color: app.theme_cls.primary_color
    mode: "rectangle"
    font_name: "assets/fonts/Hack-Regular.ttf"
    font_size: '14sp'
    multiline: False
    size_hint_y: None
    height: dp(48)

<CustomTextArea>:
    background_color: get_color_from_hex('#1e1e1e')
    foreground_color: get_color_from_hex('#00ff99')
    cursor_color: get_color_from_hex('#00ff99')
    font_name: "assets/fonts/Hack-Regular.ttf"
    font_size: '12sp'
    selection_color: get_color_from_hex('#00ff99')
    hint_text_color: get_color_from_hex('#666666')

<TerminalOutput>:
    text: ''
    font_name: "assets/fonts/Hack-Regular.ttf"
    font_size: '12sp'
    background_color: 0, 0, 0, 1
    foreground_color: get_color_from_hex('#00ff99')
    padding: dp(10), dp(10)
    size_hint_y: None
    height: self.minimum_height
    markup: True

<ScanResultCard>:
    orientation: 'vertical'
    size_hint: None, None
    size: dp(300), dp(200)
    elevation: 5
    md_bg_color: get_color_from_hex('#1e1e1e')
    padding: dp(10)
    spacing: dp(10)
    
    MDLabel:
        text: root.title
        font_style: 'H6'
        theme_text_color: 'Custom'
        text_color: get_color_from_hex('#00ff99')
        halign: 'center'
    
    MDSeparator:
        color: get_color_from_hex('#00ff99')
    
    TerminalOutput:
        id: result_content
        text: root.content

<ScanTab>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)
    
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(10)
        
        CustomTextField:
            id: target_url
            hint_text: "Target URL"
            icon_right: "web"
        
        MDFillRoundFlatButton:
            id: scan_btn
            text: "SCAN"
            size_hint_x: None
            width: dp(100)
            on_release: app.start_scan(root.ids.target_url.text)
    
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(10)
        
        CustomTextField:
            id: headers
            hint_text: "Headers (JSON)"
            icon_right: "format-header-pound"
        
        CustomTextField:
            id: cookies
            hint_text: "Cookies"
            icon_right: "cookie"
    
    CustomTextArea:
        id: post_data
        hint_text: "POST Data (JSON)"
        size_hint_y: 0.3
    
    TerminalOutput:
        id: scan_output
        size_hint_y: 0.5
    
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(10)
        
        MDRectangleFlatButton:
            text: "Quick Scan"
            on_release: app.quick_scan(root.ids.target_url.text)
        
        MDRectangleFlatButton:
            text: "Smart Dump"
            on_release: app.smart_dump(root.ids.target_url.text)
        
        MDRectangleFlatButton:
            text: "Advanced"
            on_release: app.show_advanced_options()

<ResultsTab>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)
    
    ScrollView:
        GridLayout:
            id: results_container
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(10)
            padding: dp(10)

<TelegramTab>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)
    
    CustomTextField:
        id: bot_token
        hint_text: "Telegram Bot Token"
        icon_right: "telegram"
        text: app.telegram_token
    
    CustomTextField:
        id: chat_id
        hint_text: "Chat ID"
        icon_right: "account"
        text: app.telegram_chat_id
    
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(10)
        
        MDFillRoundFlatButton:
            text: "Test Connection"
            on_release: app.test_telegram_connection()
        
        MDFillRoundFlatButton:
            text: "Save Settings"
            on_release: app.save_telegram_settings(root.ids.bot_token.text, root.ids.chat_id.text)
    
    TerminalOutput:
        id: telegram_output
        size_hint_y: 0.5

<SettingsTab>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)
    
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        
        MDLabel:
            text: "Theme:"
            halign: 'left'
            valign: 'center'
            size_hint_x: 0.3
        
        MDRectangleFlatButton:
            id: theme_switcher
            text: "Dark"
            on_release: app.switch_theme()
            size_hint_x: 0.7
    
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        
        MDLabel:
            text: "Auto-save:"
            halign: 'left'
            valign: 'center'
            size_hint_x: 0.3
        
        MDSwitch:
            id: auto_save
            active: app.auto_save
            on_active: app.set_auto_save(self.active)
            size_hint_x: 0.7
    
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        
        MDLabel:
            text: "Auto-Telegram:"
            halign: 'left'
            valign: 'center'
            size_hint_x: 0.3
        
        MDSwitch:
            id: auto_telegram
            active: app.auto_telegram
            on_active: app.set_auto_telegram(self.active)
            size_hint_x: 0.7
    
    MDFillRoundFlatButton:
        text: "Update SQLMap"
        on_release: app.update_sqlmap()
        size_hint_y: None
        height: dp(48)
    
    MDFillRoundFlatButton:
        text: "About CmdHckSqli"
        on_release: app.show_about()
        size_hint_y: None
        height: dp(48)

<MainScreen>:
    name: 'main'
    
    BoxLayout:
        orientation: 'vertical'
        
        MDTabs:
            id: tabs
            tab_bar_height: dp(48)
            background_color: get_color_from_hex('#1e1e1e')
            
            ScanTab:
                id: scan_tab
                title: 'Scanner'
                icon: 'magnify'
            
            ResultsTab:
                id: results_tab
                title: 'Results'
                icon: 'database'
            
            TelegramTab:
                id: telegram_tab
                title: 'Telegram'
                icon: 'telegram'
            
            SettingsTab:
                id: settings_tab
                title: 'Settings'
                icon: 'cog'
'''

class CustomTextField(MDTextField):
    pass

class CustomTextArea(TextInput):
    pass

class TerminalOutput(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(text=self.on_text_change)
    
    def on_text_change(self, instance, value):
        self.height = self.texture_size[1] + dp(20)

class ScanResultCard(MDCard):
    title = StringProperty('')
    content = StringProperty('')

class ScanTab(BoxLayout, MDTabsBase):
    pass

class ResultsTab(BoxLayout, MDTabsBase):
    pass

class TelegramTab(BoxLayout, MDTabsBase):
    pass

class SettingsTab(BoxLayout, MDTabsBase):
    pass

class MainScreen(Screen):
    pass

class CmdHckSqli(MDApp):
    telegram_token = StringProperty('')
    telegram_chat_id = StringProperty('')
    auto_save = BooleanProperty(True)
    auto_telegram = BooleanProperty(False)
    current_theme = StringProperty('Dark')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon_paths = {
            'telegram': 'assets/icons/telegram.png',
            'dump': 'assets/icons/dump.png',
            'settings': 'assets/icons/settings.png',
            'scanner': 'assets/icons/scanner.png'
        }
    
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Dark"
        self.title = "CmdHckSqli - SQL Injection Scanner"
        self.icon = self.icon_paths['scanner']
        
        self.load_settings()
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(MainScreen(name='main'))
        
        self.sqlmap = SQLMapWrapper(self)
        self.telegram_bot = TelegramBot(self)
        
        return Builder.load_string(KV)
    
    def load_settings(self):
        try:
            if not os.path.exists('settings.json'):
                self.create_default_settings()
            
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.apply_settings(settings)
                
        except Exception as e:
            self.show_error(f"Settings Error: {str(e)}")
            self.create_default_settings()
    
    def create_default_settings(self):
        default_settings = {
            'telegram_token': '',
            'telegram_chat_id': '',
            'auto_save': True,
            'auto_telegram': False,
            'theme': 'Dark'
        }
        with open('settings.json', 'w') as f:
            json.dump(default_settings, f)
    
    def apply_settings(self, settings):
        self.telegram_token = settings.get('telegram_token', '')
        self.telegram_chat_id = settings.get('telegram_chat_id', '')
        self.auto_save = settings.get('auto_save', True)
        self.auto_telegram = settings.get('auto_telegram', False)
        self.current_theme = settings.get('theme', 'Dark')
        
        if self.current_theme == 'Light':
            self.theme_cls.theme_style = "Light"
    
    def save_settings(self):
        try:
            settings = {
                'telegram_token': self.telegram_token,
                'telegram_chat_id': self.telegram_chat_id,
                'auto_save': self.auto_save,
                'auto_telegram': self.auto_telegram,
                'theme': self.current_theme
            }
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            self.show_error(f"Save Error: {str(e)}")
    
    def save_telegram_settings(self, token, chat_id):
        if not token or not chat_id:
            self.show_error("Token and Chat ID are required!")
            return
            
        self.telegram_token = token
        self.telegram_chat_id = chat_id
        self.save_settings()
        self.show_success("Telegram settings saved!")
    
    def set_auto_save(self, value):
        self.auto_save = value
        self.save_settings()
    
    def set_auto_telegram(self, value):
        self.auto_telegram = value
        self.save_settings()
    
    def switch_theme(self):
        if self.current_theme == 'Dark':
            self.theme_cls.theme_style = "Light"
            self.current_theme = 'Light'
            self.root.ids.settings_tab.ids.theme_switcher.text = "Light"
        else:
            self.theme_cls.theme_style = "Dark"
            self.current_theme = 'Dark'
            self.root.ids.settings_tab.ids.theme_switcher.text = "Dark"
        self.save_settings()
    
    def test_telegram_connection(self):
        if not self.telegram_token or not self.telegram_chat_id:
            self.show_error("Please enter both Bot Token and Chat ID")
            return
        
        def test_connection():
            try:
                success, message = self.telegram_bot.test_connection()
                Clock.schedule_once(lambda dt: self.show_success(message) if success else self.show_error(message))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_error(f"Connection Error: {str(e)}"))
        
        threading.Thread(target=test_connection, daemon=True).start()
    
    def validate_scan_inputs(self, target_url, headers, post_data):
        if not target_url:
            self.show_error("Target URL is required!")
            return False
        
        try:
            if headers: json.loads(headers)
            if post_data: json.loads(post_data)
            return True
        except json.JSONDecodeError:
            self.show_error("Invalid JSON format")
            return False
    
    def start_scan(self, target_url):
        tab = self.root.ids.scan_tab
        if not self.validate_scan_inputs(target_url, tab.ids.headers.text, tab.ids.post_data.text):
            return
        
        scan_options = {
            'url': target_url,
            'headers': json.loads(tab.ids.headers.text) if tab.ids.headers.text else {},
            'cookies': tab.ids.cookies.text or '',
            'data': json.loads(tab.ids.post_data.text) if tab.ids.post_data.text else {},
            'level': 3,
            'risk': 2
        }
        
        self.show_loading("Starting scan...")
        tab.ids.scan_btn.disabled = True
        
        def scan_thread():
            try:
                self.sqlmap.run_scan(scan_options)
                if self.auto_telegram and self.telegram_token and self.telegram_chat_id:
                    self.telegram_bot.send_message(f"Scan completed for {target_url}")
            except Exception as e:
                self.show_error(f"Scan Error: {str(e)}")
            finally:
                Clock.schedule_once(lambda dt: setattr(tab.ids.scan_btn, 'disabled', False))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def quick_scan(self, target_url):
        if not target_url:
            self.show_error("Target URL is required!")
            return
        
        self.show_loading("Quick scan starting...")
        
        def quick_scan_thread():
            try:
                self.sqlmap.run_scan({
                    'url': target_url,
                    'batch': True,
                    'level': 1,
                    'risk': 1
                })
            except Exception as e:
                self.show_error(f"Quick Scan Error: {str(e)}")
        
        threading.Thread(target=quick_scan_thread, daemon=True).start()
    
    def smart_dump(self, target_url):
        if not target_url:
            self.show_error("Target URL is required!")
            return
        
        self.show_loading("Smart dump starting...")
        
        def dump_thread():
            try:
                self.sqlmap.run_scan({
                    'url': target_url,
                    'batch': True,
                    'dump-all': True,
                    'threads': 3
                })
            except Exception as e:
                self.show_error(f"Dump Error: {str(e)}")
        
        threading.Thread(target=dump_thread, daemon=True).start()
    
    def show_advanced_options(self):
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(200))
        content.add_widget(Label(text="Advanced Scan Options", size_hint_y=None, height=dp(40)))
        
        options = [
            "Level (1-5): 3",
            "Risk (1-3): 2",
            "Threads: 3",
            "Batch mode: Yes",
            "Verbose: 3"
        ]
        
        for option in options:
            content.add_widget(Label(text=option, size_hint_y=None, height=dp(30)))
        
        self.adv_dialog = MDDialog(
            title="Advanced Options",
            type="custom",
            content_cls=content,
            buttons=[
                MDRectangleFlatButton(text="CANCEL", on_release=lambda x: self.adv_dialog.dismiss()),
                MDFillRoundFlatButton(text="START", on_release=self.start_advanced_scan)
            ]
        )
        self.adv_dialog.open()
    
    def start_advanced_scan(self, *args):
        self.adv_dialog.dismiss()
        target_url = self.root.ids.scan_tab.ids.target_url.text
        if target_url:
            self.start_scan(target_url)
    
    def update_sqlmap(self):
        self.show_loading("Updating SQLMap...")
        
        def update_thread():
            try:
                result = self.sqlmap.update()
                Clock.schedule_once(lambda dt: self.show_success("SQLMap updated!") if result else self.show_error("Update failed"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_error(f"Update Error: {str(e)}"))
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def show_about(self):
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(150))
        content.add_widget(Label(text="CmdHckSqli v1.0", size_hint_y=None, height=dp(40)))
        content.add_widget(Label(text="SQL Injection Scanner", size_hint_y=None, height=dp(30)))
        content.add_widget(Label(text="© 2023 Your Name", size_hint_y=None, height=dp(30)))
        
        MDDialog(
            title="About",
            type="custom",
            content_cls=content,
            buttons=[MDFillRoundFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
        ).open()
    
    def show_loading(self, message):
        Snackbar(text=message).open()
    
    def show_success(self, message):
        Snackbar(text=message, bg_color=get_color_from_hex('#00C853')).open()
    
    def show_error(self, message):
        Snackbar(text=message, bg_color=get_color_from_hex('#FF5252'), duration=3).open()
    
    def update_output(self, text):
        Clock.schedule_once(lambda dt: setattr(self.root.ids.scan_tab.ids.scan_output, 'text', text))
    
    def add_result(self, title, content):
        card = ScanResultCard(title=title, content=content)
        Clock.schedule_once(lambda dt: self.root.ids.results_tab.ids.results_container.add_widget(card))
    
    def save_result(self, title, content):
        if not self.auto_save:
            return
        
        try:
            os.makedirs('/sdcard/SQLiScanner', exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/sdcard/SQLiScanner/result_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"=== {title} ===\n\n{content}")
            
            self.show_success(f"Saved to {filename}")
        except Exception as e:
            self.show_error(f"Save Error: {str(e)}")

if __name__ == '__main__':
    CmdHckSqli().run()