import os
import subprocess
import time
from datetime import datetime
from kivy.clock import Clock

class SQLMapWrapper:
    def __init__(self, app):
        self.app = app
        self.process = None
        self.output_file = None
        self.running = False
    
    def run_scan(self, options):
        self.running = True
        try:
            # Prepare command
            cmd = ["python", "libs/sqlmap/sqlmap.py", "-u", options['url'], "--batch"]
            
            # Add headers if provided
            if options.get('headers'):
                headers = ",".join([f"{k}:{v}" for k, v in options['headers'].items()])
                cmd.extend(["--headers", headers])
            
            # Add cookies if provided
            if options.get('cookies'):
                cmd.extend(["--cookie", options['cookies']])
            
            # Add POST data if provided
            if options.get('data'):
                cmd.extend(["--data", json.dumps(options['data'])])
            
            # Add level and risk
            cmd.extend(["--level", str(options.get('level', 3))])
            cmd.extend(["--risk", str(options.get('risk', 2))])
            
            # Add other options
            if options.get('dump-all', False):
                cmd.append("--dump-all")
            
            if options.get('threads'):
                cmd.extend(["--threads", str(options['threads'])])
            
            # Create output directory if needed
            if not os.path.exists('/sdcard/SQLiScanner'):
                os.makedirs('/sdcard/SQLiScanner')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = f"/sdcard/SQLiScanner/scan_{timestamp}.txt"
            
            # Run SQLMap
            Clock.schedule_once(lambda dt: self.app.show_loading("Scanning target..."))
            
            with open(self.output_file, 'w') as f:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                for line in self.process.stdout:
                    Clock.schedule_once(lambda dt, line=line: self.app.update_output(line.strip()))
                    f.write(line)
            
            # Process completed
            self.process.wait()
            
            if self.process.returncode == 0:
                Clock.schedule_once(lambda dt: self.app.show_success("Scan completed!"))
                
                # Add to results
                with open(self.output_file, 'r') as f:
                    content = f.read()
                    Clock.schedule_once(lambda dt: self.app.add_result(f"Scan Result {timestamp}", content))
                
                # Auto-send to Telegram if enabled
                if self.app.auto_telegram and self.app.telegram_token and self.app.telegram_chat_id:
                    Clock.schedule_once(lambda dt: self.app.telegram_bot.send_message(f"SQLi Scan completed for {options['url']}"))
                    Clock.schedule_once(lambda dt: self.app.telegram_bot.send_document(self.output_file, "Scan results"))
            else:
                Clock.schedule_once(lambda dt: self.app.show_error("Scan failed"))
        
        except Exception as e:
            Clock.schedule_once(lambda dt: self.app.show_error(f"Scan error: {str(e)}"))
        
        finally:
            self.running = False
    
    def update(self):
        try:
            # Check if git is available
            try:
                subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except:
                return False
            
            # Update SQLMap
            if os.path.exists("libs/sqlmap/.git"):
                result = subprocess.run(
                    ["git", "-C", "libs/sqlmap", "pull"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if result.returncode == 0:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print(f"Update error: {str(e)}")
            return False
    
    def stop_scan(self):
        if self.process and self.running:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            
            self.running = False
            return True
        return False
