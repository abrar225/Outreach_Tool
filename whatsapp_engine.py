"""
FireHox WhatsApp Outreach Engine - Backend Logic
FIXED: Singleton Lock Issue with Open-Close-Reopen Architecture
"""

import pandas as pd
import phonenumbers
from phonenumbers import NumberParseException
import random
import time
from urllib.parse import quote
import os
import shutil
import sys
import asyncio
import subprocess

# ==================== PYTHON 3.13 COMPATIBILITY FIX ====================
if sys.platform == 'win32' and sys.version_info >= (3, 13):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

# Constants - Isolated Session Directory
USER_DATA_DIR = "./firehox_wa_session"


class WhatsAppBot:
    """WhatsApp automation bot with Open-Close-Reopen architecture"""
    
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None
    
    @staticmethod
    def force_browser_cleanup():
        """
        CRITICAL: Force cleanup of any zombie browser processes and locks
        This MUST be called before launching browser to prevent SingletonLock errors
        Returns: (success: bool, message: str)
        """
        try:
            print("🧹 Starting browser cleanup...")
            
            # Step 1: Check for SingletonLock file
            lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
            
            if os.path.exists(lock_file):
                print(f"⚠️ Found lock file: {lock_file}")
                
                # Retry removing the lock file a few times with backoff
                for attempt in range(3):
                    try:
                        os.remove(lock_file)
                        print("✅ Successfully removed lock file")
                        break
                    except PermissionError:
                        if attempt < 2:
                            print(f"⚠️ Lock file is in use, retrying in {attempt + 1}s...")
                            time.sleep(attempt + 1)
                        else:
                            # Final attempt: try platform-specific cleanup of Playwright chromium only
                            print("⚠️ Lock file still in use. Attempting to close Playwright browser...")
                            try:
                                if sys.platform == 'win32':
                                    # Only kill chromium (Playwright's browser), not user's Chrome
                                    subprocess.run(
                                        "taskkill /F /IM chromium.exe",
                                        shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                                    )
                                else:
                                    # Linux/Mac
                                    subprocess.run(
                                        ["pkill", "-f", "chromium"],
                                        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                                    )
                                
                                time.sleep(2)
                                if os.path.exists(lock_file):
                                    os.remove(lock_file)
                                print("✅ Playwright browser closed and lock file removed.")
                            except Exception as kill_err:
                                return False, (
                                    "🔒 Browser is locked and could not be force-closed.\n"
                                    "Please close the Chromium browser window manually and try again.\n"
                                    f"Error: {kill_err}"
                                )
            
            # Step 2: Wait a moment for OS to release resources
            time.sleep(1)
            
            return True, "✅ Cleanup successful"
            
        except Exception as e:
            return False, f"❌ Cleanup error: {str(e)}"
    
    def launch_browser(self):
        """
        Launch isolated persistent browser context
        
        Returns: (success: bool, message: str, page: Page object or None)
        """
        try:
            # CRITICAL: Force cleanup before launching
            cleanup_success, cleanup_msg = self.force_browser_cleanup()
            if not cleanup_success:
                return False, cleanup_msg, None
            
            # Reset instances
            self.page = None
            self.context = None
            self.playwright = None
            
            # Create user data directory
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            
            # Start Playwright with Python 3.13 compatibility
            try:
                self.playwright = sync_playwright().start()
            except NotImplementedError:
                return False, "❌ Python 3.13 Compatibility Issue!\n\nPlaywright doesn't fully support Python 3.13 yet.\n\nPlease install Python 3.12 from:\nhttps://www.python.org/downloads/\n\nSee PYTHON_313_FIX.md for detailed instructions.", None
            
            # Launch persistent context
            try:
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_DIR,
                    headless=False,
                    viewport=None,  # Maximize window
                    args=[
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-extensions',
                        '--no-first-run',
                    ],
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    accept_downloads=False,
                    ignore_https_errors=True,
                    java_script_enabled=True
                )
            except PlaywrightError as e:
                error_msg = str(e).lower()
                if "target closed" in error_msg or "singleton" in error_msg or "lock" in error_msg:
                    return False, "🔒 Browser is locked. Please close any open Chromium windows manually and try again.", None
                else:
                    return False, f"❌ Browser launch error: {str(e)[:200]}", None
            
            # Get or create page
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
            # Navigate to WhatsApp Web
            self.page.goto("https://web.whatsapp.com", timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)
            
            return True, "✅ Browser launched successfully! Please scan QR code if prompted.", self.page
            
        except Exception as e:
            # Cleanup on error
            try:
                if self.playwright:
                    self.playwright.stop()
            except Exception:
                pass
            return False, f"❌ Unexpected error: {str(e)[:200]}", None
    
    def verify_login(self, timeout=30):
        """
        Verify if user is logged into WhatsApp Web
        Returns: (logged_in: bool, message: str)
        """
        if not self.page:
            return False, "No browser page available"
        
        try:
            print("⏳ Verifying WhatsApp Web login status...")
            
            # Selectors specific to logged-in state
            logged_in_selectors = [
                '#side',
                'div[data-testid="chat-list"]',
                'header[data-testid="chatlist-header"]',
                'span[data-icon="search"]'
            ]
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                for selector in logged_in_selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            if self.page.locator(selector).first.is_visible():
                                return True, "✅ Successfully logged in!"
                    except Exception:
                        pass
                time.sleep(1)
            
            return False, "⏱️ Login verification timed out. If you see chats, use 'Skip Verification'."
            
        except Exception as e:
            return False, f"❌ Verification error: {str(e)}"
    
    def close_browser(self):
        """
        Safely close browser and release the SingletonLock
        """
        try:
            print("🔒 Closing browser...")
            if self.page: self.page.close()
            if self.context: self.context.close()
            if self.playwright: self.playwright.stop()
            
            self.page = None
            self.context = None
            self.playwright = None
            
            time.sleep(2) # Allow OS to release file locks
            return True, "✅ Browser closed successfully"
        except Exception as e:
            return False, f"⚠️ Error closing browser: {str(e)}"
    
    def reset_session(self):
        """Reset the browser session by deleting user data directory"""
        try:
            close_success, close_msg = self.close_browser()
            if not close_success:
                print(f"⚠️ Browser close warning: {close_msg}")
            time.sleep(2)
            if os.path.exists(USER_DATA_DIR):
                shutil.rmtree(USER_DATA_DIR)
                return True, "✅ Session reset successfully."
            return True, "✅ No session data found."
        except Exception as e:
            return False, f"❌ Error resetting session: {str(e)}"

    @staticmethod
    def wait_with_countdown(min_seconds, max_seconds, callback=None):
        """
        Wait for a random duration with countdown callback
        """
        delay = random.randint(min_seconds, max_seconds)
        for i in range(delay, 0, -1):
            if callback:
                callback(i)
            time.sleep(1)
    
    @staticmethod
    def clean_data(dataframe, default_country_code="+91", phone_col=None, name_col=None):
        """
        Clean and validate phone number data with robust column detection
        """
        if dataframe is None or dataframe.empty:
            return None, {"error": "Empty dataframe provided"}
        
        df = dataframe.copy()
        
        # Column Discovery (Robust) or Manual Override
        target_phone = phone_col
        target_name = name_col
        
        cols = [c.lower() for c in df.columns]
        
        # 1. Phone Detection (If not provided)
        if not target_phone:
            phone_keywords = ['phone', 'mobile', 'contact', 'tel', 'number', 'whatsapp', 'cell', 'digits', 'ph']
            for i, col in enumerate(cols):
                if any(key == col for key in phone_keywords): # Prioritize exact match
                    target_phone = df.columns[i]
                    break
            
            if not target_phone:
                for i, col in enumerate(cols):
                    if any(key in col for key in phone_keywords):
                        target_phone = df.columns[i]
                        break

        # 2. Name Detection (If not provided - Excludes 'unnamed')
        if not target_name:
            name_keywords = ['business', 'company', 'name', 'client', 'customer', 'lead', 'title', 'shop', 'cafe', 'restaurant', 'store']
            
            # Filter out 'unnamed' columns from potential names
            valid_name_cols = [c for c in df.columns if 'unnamed' not in c.lower()]
            
            # Priority 1: Exact matches
            for col in valid_name_cols:
                if col.lower() in ['business name', 'name', 'business', 'company name']:
                    target_name = col
                    break
            
            # Priority 2: Keyword matches
            if not target_name:
                for col in valid_name_cols:
                    if any(key in col.lower() for key in name_keywords):
                        target_name = col
                        break
        
        # Defaults if not found
        if not target_phone:
            # Try to find a column with many digits
            for col in df.columns:
                sample = str(df[col].iloc[0]) if len(df) > 0 else ""
                digits = ''.join(c for c in sample if c.isdigit())
                if len(digits) >= 10:
                    target_phone = col
                    break
        
        if not target_phone:
            return None, {"error": "❌ Could not identify the Phone Number column. Please rename it manually to 'Phone'."}
        
        if not target_name:
            # Default to the first column that isn't the phone column
            for col in df.columns:
                if col != target_phone:
                    target_name = col
                    break
        
        if not target_name:
            target_name = target_phone # Last resort
            
        # Data Cleaning
        df[target_phone] = df[target_phone].astype(str).str.strip()
        df[target_name] = df[target_name].astype(str).str.strip()
        
        # Explicitly handle 'Unnamed' columns to avoid Arrow serialization issues
        for col in df.columns:
            if 'unnamed' in col.lower():
                df[col] = df[col].astype(str)
        
        # Filter out obvious errors
        df = df[df[target_phone].notna()]
        df = df[df[target_phone].str.strip() != '']
        df = df[df[target_phone] != 'nan']
        df = df.drop_duplicates(subset=[target_phone])

        initial_count = len(df)
        
        cleaned_phones = []
        cleaned_names = []
        statuses = []
        
        for _, row in df.iterrows():
            phone = str(row[target_phone]).strip()
            name = str(row[target_name]).strip()
            
            # Remove common junk from name (like .csv, numbers if they are just the phone)
            if name.lower().endswith('.csv'):
                name = name[:-4]
            
            # Basic phone cleanup
            phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
            
            if len(phone_clean.replace('+', '')) < 5:
                continue
            
            try:
                # Append default country code if missing
                if not phone_clean.startswith('+'):
                    # Handle cases where number already has country code but no '+'
                    if len(phone_clean) > 10 and not phone_clean.startswith('0'):
                        phone_clean = '+' + phone_clean
                    else:
                        phone_clean = default_country_code + phone_clean
                
                parsed = phonenumbers.parse(phone_clean, None)
                if phonenumbers.is_valid_number(parsed):
                    formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                    cleaned_phones.append(formatted)
                    cleaned_names.append(name if name and name.lower() != 'nan' else "Business Owner")
                    statuses.append("Valid")
                else:
                    cleaned_phones.append(phone_clean)
                    cleaned_names.append(name)
                    statuses.append("Invalid (Format)")
            except NumberParseException:
                cleaned_phones.append(phone_clean)
                cleaned_names.append(name)
                statuses.append("Invalid (Parse Error)")
        
        cleaned_df = pd.DataFrame({
            'Name': cleaned_names,
            'Phone': cleaned_phones,
            'Status': statuses
        })
        
        if cleaned_df.empty:
             return None, {"error": "No valid data after cleaning"}

        valid_df = cleaned_df[cleaned_df['Status'] == 'Valid'].copy()
        
        report = {
            'total_rows': initial_count,
            'valid_rows': len(valid_df),
            'invalid_rows': len(cleaned_df) - len(valid_df),
            'removed_rows': initial_count - len(valid_df),
            'phone_column': target_phone,
            'name_column': target_name
        }
        
        return valid_df, report
    
    def generate_message(self, business_name):
        """
        Generate high-converting personalized message with 4 distinct variations
        Focus: Google Reviews + No Website -> Demo Website Pitch (Universal)
        """
        # Ensure business_name is professional
        if not business_name or business_name.lower() in ['nan', 'none', 'unknown']:
            name_display = "your business"
        else:
            name_display = business_name
            
        # Template 1: Premium Solution
        t1 = f"""Hello {name_display} 👋

I was browsing your listing on Google and noticed you have some fantastic reviews from customers! However, I couldn't find a website linked to your business.

In today's digital world, having a professional site is the best way to turn those Google searches into high-paying clients.

I've actually taken the liberty of designing a **exclusive demo website specifically for {name_display}** to show you how your brand could look online.

It features:
✅ Ultra-fast loading
✅ Perfect mobile viewing
✅ Direct contact buttons

Would you be open to seeing the demo link? (No cost or obligation)"""

        # Template 2: Opportunity Peak
        t2 = f"""Hi Team {name_display}! 🚀

I came across your profile on Google Maps today. You're clearly doing great work based on your reviews, but I noticed a major missing piece: an official website.

I specialize in building digital presence for businesses. I've already put together a **preview website for {name_display}** to show you what you're currently missing out on.

I'd love to share the link with you to get your feedback.

Shall I send it over?"""

        # Template 3: Market Presence
        t3 = f"""Greetings {name_display},

I'm Abrar from FireHox. While researching top-rated businesses in your sector, your profile stood out.

You have a great reputation, but missing a website is likely losing you 30-40% of potential customers who want to see your services online before calling.

I’ve already developed a **premium website concept for {name_display}** that solves this. It's fully functional and ready for you to preview.

Would you like to see how it looks?"""

        # Template 4: Modernization
        t4 = f"""Hey {name_display}! 👋

Just wanted to reach out because your Google reviews are impressive! ⭐️ 

I noticed you don't have a modern website yet, so I created a **concept design specifically for {name_display}** that truly matches the quality of your work.

It makes it incredibly easy for new customers to trust you and book your services.

I'd love to show you the demo if you have a minute? Let me know!"""

        templates = [t1, t2, t3, t4]
        return random.choice(templates)
    
    def _check_invalid_number(self):
        """
        Check if WhatsApp is showing an 'invalid number' or 'not on WhatsApp' popup.
        Returns True if an invalid number indicator is detected, False otherwise.
        Also clicks the OK/Close button to dismiss the popup if found.
        """
        if not self.page:
            return False
        
        # All known invalid-number indicators on WhatsApp Web
        invalid_selectors = [
            "div[data-testid='invalid-number']",
            "text=Phone number shared via url is invalid",
            "text=The phone number is invalid",
            "text=isn't on WhatsApp",                    # "The number +91... isn't on WhatsApp."
            "text=not on WhatsApp",                       # Alternative wording
            "text=number is not registered",              # Older variants
        ]
        
        for selector in invalid_selectors:
            try:
                loc = self.page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible():
                    print(f"🚫 Invalid number detected via: {selector}")
                    # Try to dismiss the popup by clicking OK
                    self._dismiss_popup()
                    return True
            except Exception:
                continue
        
        return False
    
    def _dismiss_popup(self):
        """Click the OK button on WhatsApp popups to dismiss them."""
        dismiss_selectors = [
            'div[role="button"]:has-text("OK")',
            'button:has-text("OK")',
            'div[data-testid="popup-controls-ok"]',
            'div[role="dialog"] div[role="button"]',
        ]
        for selector in dismiss_selectors:
            try:
                loc = self.page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible():
                    loc.first.click()
                    time.sleep(1)
                    return
            except Exception:
                continue

    def send_message(self, phone, message):
        """
        Send message using HUMAN-LIKE TYPING simulation with enhanced selectors
        Returns: (status: str, timestamp: str)
        """
        if not self.page:
            return "Failed (No browser)", time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Construct URL
            url = f"https://web.whatsapp.com/send?phone={phone}"
            
            # Go to URL
            self.page.goto(url, timeout=45000, wait_until="domcontentloaded")
            
            # Wait for specific elements to confirm page is usable
            # We wait for either the chat list, the chat box, or an error message
            try:
                self.page.wait_for_selector('div[data-testid="chat-list"], div[data-testid="invalid-number"], div[role="dialog"]', timeout=15000)
            except Exception:
                pass  # Continue anyway, sometimes selectors flake
            
            # 1. Check for Invalid Number (first pass)
            invalid_detected = self._check_invalid_number()
            if invalid_detected:
                return "Failed (Invalid Number)", time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 2. Wait for Input Box (Robust)
            input_box = None
            input_selectors = [
                 'div[contenteditable="true"][data-tab="10"]',
                 'div[aria-label="Type a message"]',
                 'div[title="Type a message"]',
                 'div.lexical-rich-text-input div[contenteditable="true"]',
                 '#main footer div[contenteditable="true"]'
            ]
            
            # Try to find input box with retries
            for attempt in range(3): # 3 attempts
                # Re-check for invalid number popup on each retry
                # (the popup often appears AFTER a delay)
                invalid_detected = self._check_invalid_number()
                if invalid_detected:
                    return "Failed (Invalid Number)", time.strftime("%Y-%m-%d %H:%M:%S")
                
                for selector in input_selectors:
                    try:
                        loc = self.page.locator(selector)
                        if loc.count() > 0 and loc.first.is_visible():
                            input_box = loc.first
                            break
                    except Exception:
                        continue
                if input_box: break
                time.sleep(2)
            
            if not input_box:
                # One final invalid number check before giving up
                invalid_detected = self._check_invalid_number()
                if invalid_detected:
                    return "Failed (Invalid Number)", time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Urgent Fallback: Click on the main chat area if possible
                try:
                    self.page.click('#main footer', timeout=5000)
                    time.sleep(1)
                    # Re-search
                    for selector in input_selectors:
                        loc = self.page.locator(selector)
                        if loc.count() > 0:
                            input_box = loc.first
                            break
                except Exception:
                    pass

            if not input_box:
                print("⚠️ Input box not found, falling back to URL injection.")
                encoded_message = quote(message)
                url_with_text = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
                self.page.goto(url_with_text, timeout=30000)
                time.sleep(5)
                
                # Check for invalid number AGAIN after URL reload
                invalid_detected = self._check_invalid_number()
                if invalid_detected:
                    return "Failed (Invalid Number)", time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Try to find input box after URL injection
                fallback_input = None
                for selector in input_selectors:
                    try:
                        loc = self.page.locator(selector)
                        if loc.count() > 0 and loc.first.is_visible():
                            fallback_input = loc.first
                            break
                    except Exception:
                        continue
                
                if not fallback_input:
                    return "Failed (No chat loaded)", time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Clear and re-type
                fallback_input.click()
                time.sleep(0.5)
                self.page.keyboard.press("Control+A") # Select any existing text
                self.page.keyboard.press("Backspace") # Clear
                
                # Typing with Shift+Enter handling
                lines = message.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() != "":
                        self.page.keyboard.type(line, delay=random.randint(5, 12))
                    if i < len(lines) - 1:
                        self.page.keyboard.press("Shift+Enter")
                time.sleep(2)
            else:
                # Input box found -> TYPE MESSAGE
                input_box.click()
                time.sleep(1)
                
                # Human-like typing with Shift+Enter handling for newlines
                lines = message.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() != "":
                        self.page.keyboard.type(line, delay=random.randint(5, 12))
                    
                    if i < len(lines) - 1:
                        # In WhatsApp Web, Enter sends. Shift+Enter adds a newline.
                        self.page.keyboard.press("Shift+Enter")
                        time.sleep(random.uniform(0.1, 0.3))
                        
                time.sleep(random.uniform(1.5, 3))
            
            # 3. Locate and Click Send Button
            # We try multiple times because the button can take a split second to activate after typing
            send_button = None
            send_button_selectors = [
                'span[data-icon="send"]',
                'button[aria-label="Send"]',
                'button[data-testid="send"]',
                'div[data-testid="send"]',
                '#main footer button span[data-icon="send"]',
                'footer button'
            ]
            
            for _ in range(5): # Up to 5 retries for the button
                for selector in send_button_selectors:
                    try:
                        loc = self.page.locator(selector)
                        if loc.count() > 0 and loc.first.is_visible():
                            send_button = loc.first
                            break
                    except Exception: continue
                if send_button: break
                time.sleep(1)
            
            if send_button:
                time.sleep(random.uniform(1, 2)) # Human pause
                send_button.click()
                time.sleep(3) # Wait for message to move to chat
            else:
                # Try pressing ENTER as a last resort
                # Make sure we're focused on the input
                if input_box: input_box.click() 
                self.page.keyboard.press("Enter")
                time.sleep(3)
            
            # 4. Post-send: check one more time for "not on WhatsApp" popup
            # (WhatsApp sometimes shows this AFTER you try to send)
            invalid_detected = self._check_invalid_number()
            if invalid_detected:
                return "Failed (Not on WhatsApp)", time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 5. FINAL VERIFICATION: Check for sent tick marks in the CURRENT conversation only
            # Look specifically inside #main to avoid matching ticks from other chats
            success_indicators = [
                '#main span[data-icon="msg-check"]',      # Single tick
                '#main span[data-icon="msg-dblcheck"]',   # Double tick
                '#main span[data-icon="msg-dblcheck-ack"]'# Blue ticks
            ]
            
            for selector in success_indicators:
                try:
                    if self.page.locator(selector).count() > 0:
                        return "Sent ✅", time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue
            
            # If we reached here, we sent it but can't see the tick yet (slow network)
            return "Sent (Pending) ⏳", time.strftime("%Y-%m-%d %H:%M:%S")
                
        except PlaywrightTimeout:
            return "Failed (Timeout)", time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            return f"Failed ({str(e)[:50]})", time.strftime("%Y-%m-%d %H:%M:%S")
