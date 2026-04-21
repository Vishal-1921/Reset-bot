import os
os.environ['TERM'] = 'xterm'
import re
import requests
import random
import string
import asyncio
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient, events
from user_agent import generate_user_agent

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
BOT_TOKEN = "8612515670:AAFR2DU_RHhDd5QPs0lNgJBiJneyeFb5BD0"
MAX_WORKERS = 50
ADMIN_ID = 1725301348
CONTACT_LINK = "https://t.me/HloSpidey"
CHANNEL_LINK = "https://t.me/SpideyStuff"

GOOGLE_ACCOUNTS_URL = 'https://accounts.google.com'
GOOGLE_ACCOUNTS_DOMAIN = 'accounts.google.com'

class TokenManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.token = None
                    cls._instance.host_cookie = None
                    cls._instance.token_lock = threading.Lock()
        return cls._instance
    
    def get_token(self):
        with self.token_lock:
            return self.token, self.host_cookie
    
    def set_token(self, token, host_cookie):
        with self.token_lock:
            self.token = token
            self.host_cookie = host_cookie

class GmailAvailabilityChecker:
    def __init__(self):
        self.token_manager = TokenManager()
        self.session_pool = queue.Queue()
        self._init_session_pool()
        self.token_refresh_lock = threading.Lock()
        self._create_new_token()  # Generate token once at startup
    
    def _init_session_pool(self, pool_size=30):  # Increased to 30 for threads
        for _ in range(pool_size):
            session = requests.Session()
            session.headers.update({
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
            })
            self.session_pool.put(session)
    
    def _get_session(self):
        try:
            return self.session_pool.get(timeout=1)
        except:
            return requests.Session()
    
    def _return_session(self, session):
        try:
            self.session_pool.put(session)
        except:
            pass
    
    def _create_new_token(self):
        """Generate a single token to be reused by all threads"""
        try:
            alphabet = 'azertyuiopmlkjhgfdsqwxcvbn'
            n1 = ''.join(random.choice(alphabet) for _ in range(random.randint(6, 9)))
            n2 = ''.join(random.choice(alphabet) for _ in range(random.randint(3, 9)))
            host = ''.join(random.choice(alphabet) for _ in range(random.randint(15, 30)))
            
            headers = {
                'accept': '*/*',
                'accept-language': 'ar-IQ,ar;q=0.9,en-IQ;q=0.8,en;q=0.7,en-US;q=0.6',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'google-accounts-xsrf': '1',
                'user-agent': str(generate_user_agent())
            }
            
            recovery_url = f"{GOOGLE_ACCOUNTS_URL}/signin/v2/usernamerecovery?flowName=GlifWebSignIn&flowEntry=ServiceLogin&hl=en-GB"
            res1 = requests.get(recovery_url, headers=headers)
            
            match = re.search('data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&', res1.text)
            
            if match:
                tok = match.group(2)
                cookies = {'__Host-GAPS': host}
                
                headers2 = {
                    'authority': GOOGLE_ACCOUNTS_DOMAIN,
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'google-accounts-xsrf': '1',
                    'origin': GOOGLE_ACCOUNTS_URL,
                    'referer': 'https://accounts.google.com/signup/v2/createaccount?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&theme=mn',
                    'user-agent': generate_user_agent()
                }
                
                data = {
                    'f.req': f'["{tok}","{n1}","{n2}","{n1}","{n2}",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
                    'deviceinfo': '[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]'
                }
                
                response = requests.post(f"{GOOGLE_ACCOUNTS_URL}/_/signup/validatepersonaldetails",
                                        cookies=cookies, headers=headers2, data=data)
                
                token_parts = str(response.text).split('",null,"')
                if len(token_parts) > 1:
                    token = token_parts[1].split('"')[0]
                    host_cookie = response.cookies.get_dict().get('__Host-GAPS', host)
                    self.token_manager.set_token(token, host_cookie)
                    print(f"✅ Token generated successfully: {token[:20]}...")
                else:
                    print("❌ Failed to extract token from response")
            else:
                print("❌ Failed to find token pattern in response")
        
        except Exception as e:
            print(f"❌ Token creation error: {e}")
    
    def check_availability(self, username):
        try:
            username = username.lower().strip()
            
            if not username or len(username) < 6:
                return {'available': False, 'username': username}
            
            token, host_cookie = self.token_manager.get_token()
            if not token or not host_cookie:
                print("⚠️ No token available, attempting to create new one...")
                with self.token_refresh_lock:
                    if not self.token_manager.get_token()[0]:
                        self._create_new_token()
                        token, host_cookie = self.token_manager.get_token()
            
            session = self._get_session()
            
            try:
                cookies = {'__Host-GAPS': host_cookie}
                
                headers = {
                    'authority': GOOGLE_ACCOUNTS_DOMAIN,
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'google-accounts-xsrf': '1',
                    'origin': GOOGLE_ACCOUNTS_URL,
                    'referer': f"https://accounts.google.com/signup/v2/createusername?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&TL={token}",
                    'user-agent': generate_user_agent()
                }
                
                params = {'TL': token}
                
                data = (f"continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&ddm=0&flowEntry=SignUp&service=mail&theme=mn"
                        f"&f.req=%5B%22TL%3A{token}%22%2C%22{username}%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D"
                        "&azt=AFoagUUtRlvV928oS9O7F6eeI4dCO2r1ig%3A1712322460888&cookiesDisabled=false"
                        "&deviceinfo=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%22NL%22%2Cnull%2Cnull%2Cnull%2C%22GlifWebSignIn%22"
                        "%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C2%2Cnull%2C0%2C1%2C%22%22%2Cnull%2Cnull%2C2%2C2%5D"
                        "&gmscoreversion=undefined&flowName=GlifWebSignIn&")
                
                response = session.post(f"{GOOGLE_ACCOUNTS_URL}/_/signup/usernameavailability",
                                       params=params, cookies=cookies, headers=headers, data=data, timeout=10)
                
                if '"gf.uar",1' in response.text:
                    return {'available': True, 'username': username}
                else:
                    return {'available': False, 'username': username}
            finally:
                self._return_session(session)
                
        except Exception as e:
            return {'available': None, 'username': username}

class EmailExtractor:
    @staticmethod
    def extract_emails(text):
        valid_emails = []
        seen = set()
        
        pattern = r'[Ee]mail\s*[:：]\s*([a-zA-Z0-9._%+-]+@gmail\.com)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            email_lower = match.lower()
            username = email_lower.split('@')[0]
            if email_lower not in seen and len(username) >= 6 and re.match(r'^[a-zA-Z0-9._]+$', username):
                seen.add(email_lower)
                valid_emails.append(email_lower)
        
        if not valid_emails:
            email_pattern = r'\b([a-zA-Z0-9._]{6,}@gmail\.com)\b'
            all_emails = re.findall(email_pattern, text)
            for email in all_emails:
                email_lower = email.lower()
                username = email_lower.split('@')[0]
                if email_lower not in seen and len(username) >= 6 and re.match(r'^[a-zA-Z0-9._]+$', username):
                    seen.add(email_lower)
                    valid_emails.append(email_lower)
        
        return valid_emails

class UncCheckerBot:
    def __init__(self, api_id, api_hash, bot_token):
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.client = TelegramClient('unc_bot', api_id, api_hash)
        self.checker = GmailAvailabilityChecker()
        self.extractor = EmailExtractor()
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.processing = set()
        self.user_last_use = {}
        self.user_check_count = {}
        self.cooldown_seconds = 20
        self.bulk_limit = 20
    
    async def start(self):
        await self.client.start(bot_token=self.bot_token)
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            from telethon.tl.types import KeyboardButtonUrl as KBUrl
            from telethon.tl.custom import Button
            buttons = [
                [Button.url("Contact Me", CONTACT_LINK), Button.url("Channel", CHANNEL_LINK)]
            ]
            
            await event.reply(
                "**I'm UNC CHECKER BOT** 🚀🤖\n\n**Send Any GMAIL or Forward Gmail Hits, I'll Extract Gmail And Check 📧** ",
                buttons=buttons,
                file="https://raw.githubusercontent.com/HloSpidey/photo/refs/heads/main/ss.jpg"
            )
        
        @self.client.on(events.NewMessage)
        async def message_handler(event):
            if event.message.text and event.message.text.startswith('/'):
                return
            
            user_id = event.sender_id
            
            if user_id != ADMIN_ID:
                current_time = time.time()
                if user_id in self.user_last_use:
                    time_diff = current_time - self.user_last_use[user_id]
                    if time_diff < self.cooldown_seconds:
                        remaining = int(self.cooldown_seconds - time_diff)
                        await event.reply(f"⏳ WAIT {remaining} SECONDS FOR COOLDOWN ⏳")
                        return
                
                if user_id in self.user_check_count:
                    if self.user_check_count[user_id] >= self.bulk_limit:
                        await event.reply(f"⏳ WAIT {self.cooldown_seconds} SECONDS FOR COOLDOWN ⏳")
                        return
            
            msg_id = event.message.id
            if msg_id in self.processing:
                return
            
            self.processing.add(msg_id)
            
            try:
                text = event.message.text or event.message.raw_text
                if not text:
                    self.processing.remove(msg_id)
                    return
                
                emails = self.extractor.extract_emails(text)
                
                if not emails:
                    await event.reply("❌ **No valid Gmail Found ! Send Gmail Hits Only... Like : Spidey@gmail.com **")
                    self.processing.remove(msg_id)
                    return
                
                if user_id != ADMIN_ID:
                    if len(emails) > self.bulk_limit:
                        emails = emails[:self.bulk_limit]
                        await event.reply(f"**⚠️ Limited To {self.bulk_limit} Emails Per Batch. Checking First {self.bulk_limit}...**")
                    
                    self.user_last_use[user_id] = time.time()
                    self.user_check_count[user_id] = len(emails)
                    
                    asyncio.create_task(self.reset_cooldown(user_id))
                
                for email in emails:
                    await self.check_email(event, email)
                    
            finally:
                self.processing.remove(msg_id)
    
    async def reset_cooldown(self, user_id):
        await asyncio.sleep(self.cooldown_seconds)
        if user_id in self.user_check_count:
            self.user_check_count[user_id] = 0
    
    async def check_email(self, event, email):
        username = email.split('@')[0]
        full_email = f"{username}@gmail.com"
        
        status_msg = await event.reply(f" **Checking** `{full_email}`...🔍")
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self.checker.check_availability, username)
        
        if result['available'] is True:
            response = f"✅ **UNC :** `{full_email}` 📧"
        elif result['available'] is False:
            response = f"❗ **CREATED :** `{full_email}` 📧"
        else:
            response = f"⚠️ **ERROR :** `{full_email}` 📧 **Check Failed ! **"
        
        response += f"\n\nJoin @SpideyStuff For More Utility Bots 🤖🚀"
        
        await status_msg.edit(response)

async def main():
    bot = UncCheckerBot(API_ID, API_HASH, BOT_TOKEN)
    await bot.start()
    await bot.client.run_until_disconnected()

if __name__ == "__main__":
    try:
        from user_agent import generate_user_agent
    except ImportError:
        os.system('pip install telethon user_agent requests')
        os.execv(__file__, ['python3', __file__])
        
    os.system('clear')
    print("🚀 Bot Is Starting...")
    print("📧 Using single token for all threads")
    asyncio.run(main())
