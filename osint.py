import os
os.environ['TERM'] = 'xterm'
import requests
import time
import re
import asyncio
import json
import traceback
from collections import defaultdict
from datetime import datetime
from datetime import timezone, timedelta
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError, ChannelPrivateError, UserNotParticipantError

BOT_TOKEN = "8655956389:AAHITB8xDYmIPYDSa_dOVE4P6CZgfiR77ac"
API_ID = 6
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
ADMIN_IDS = [1725301348]
CONTACT_LINK = "https://t.me/HloSpidey"
CHANNEL_LINK = "https://t.me/+J-0a5CaeIZZiYzNl"
PHOTO_URL = "https://raw.githubusercontent.com/HloSpidey/photo/refs/heads/main/ss.jpg"
STORAGE_CHANNEL = -1003666940027
USERS_LIST_MSG_ID = 30
NUM_API = "https://hlospidey-7.vercel.app/api/number?num={}"
aadhar_API = "https://spidey-stuff.vercel.app/api/aadhar?adh={}"
FAMILY_API = "https://atof.onrender.com/full-search?aadhaar={}"

VERIFY_CHANNEL_1 = -1002744702466
VERIFY_CHANNEL_2 = -1003425131774
VERIFY_LINK_1 = "https://t.me/+J-0a5CaeIZZiYzNl"
VERIFY_LINK_2 = "https://t.me/+4CSKZ4y-v4ZiNTA1"

DEFAULT_GC_LINK = "https://t.me/+4CSKZ4y-v4ZiNTA1"
DEFAULT_CH_LINK = "https://t.me/spideystuff"

current_gc_link = DEFAULT_GC_LINK
current_ch_link = DEFAULT_CH_LINK

api_locks = {
    "num": False,
    "adh": False,
    "family": False
}

user_state = {}
user_last_command = defaultdict(float)
user_last_adh_command = defaultdict(float)
user_last_family_command = defaultdict(float)
user_invalid_attempts = defaultdict(int)
user_waiting_messages = {}
protected_numbers = defaultdict(list)
protected_aadhars = defaultdict(list)
request_count = 0
adh_request_count = 0
family_request_count = 0
request_window_start = time.time()
adh_request_window_start = time.time()
family_request_window_start = time.time()
cooldown_active = False
adh_cooldown_active = False
family_cooldown_active = False
cooldown_users = set()
adh_cooldown_users = set()
family_cooldown_users = set()
users_list = set()

broadcast_active = False
broadcast_messages = []
broadcast_status_msg = None
broadcast_sent_count = 0
broadcast_fail_count = 0
broadcast_blocked_count = 0
broadcast_deleted_count = 0
broadcast_other_errors = 0
broadcast_sent_message_ids = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def add_user(user_id):
    if user_id not in users_list and not is_admin(user_id):
        users_list.add(user_id)
        asyncio.create_task(update_users_list_msg())

def get_all_users():
    return list(users_list)

def get_user_count():
    return len(users_list)

async def update_users_list_msg():
    try:
        msg_text = "📊 **Users List** 📊\n\n"
        for uid in sorted(users_list):
            msg_text += f"👤 `{uid}`\n"
        await client.edit_message(STORAGE_CHANNEL, USERS_LIST_MSG_ID, msg_text, parse_mode='markdown')
    except Exception as e:
        print(f"Error updating users list: {e}")

async def load_users_list():
    global users_list
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=USERS_LIST_MSG_ID)
        if msg and msg.text:
            users_list = set()
            for line in msg.text.split('\n'):
                if '`' in line:
                    line = line.split('`')[1]
                line = line.strip()
                if line.isdigit():
                    users_list.add(int(line))
    except Exception as e:
        print(f"Error loading users list: {e}")
        users_list = set()

def extract_number(text):
    cleaned = re.sub(r'[\s\+\-\(\)]', '', text)
    digits = re.findall(r"\d", cleaned)
    if len(digits) >= 10:
        number = "".join(digits)
        if number.startswith('91') and len(number) > 10:
            number = number[2:]
        if len(number) > 10:
            number = number[-10:]
        return number if len(number) == 10 else None
    return None

def extract_aadhar(text):
    cleaned = re.sub(r'[\s\-]', '', text)
    digits = re.findall(r"\d", cleaned)
    if len(digits) >= 12:
        aadhar = "".join(digits)[:12]
        return aadhar if len(aadhar) == 12 else None
    return None

async def delete_message_later(msg, delay=59):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

async def delete_user_messages(user_id):
    if user_id in user_waiting_messages:
        for msg in user_waiting_messages[user_id]:
            try:
                await msg.delete()
            except:
                pass
        del user_waiting_messages[user_id]

def check_rate_limit(user_id, command_type='num'):
    if is_admin(user_id):
        return True, 0
    
    if command_type == 'num':
        last_time = user_last_command[user_id]
        elapsed = time.time() - last_time
        if elapsed < 17:
            return False, int(17 - elapsed)
        return True, 0
    elif command_type == 'adh':
        last_time = user_last_adh_command[user_id]
        elapsed = time.time() - last_time
        if elapsed < 17:
            return False, int(17 - elapsed)
        return True, 0
    else:
        last_time = user_last_family_command[user_id]
        elapsed = time.time() - last_time
        if elapsed < 17:
            return False, int(17 - elapsed)
        return True, 0

def update_rate_limit(user_id, command_type='num'):
    if is_admin(user_id):
        return
    
    if command_type == 'num':
        user_last_command[user_id] = time.time()
    elif command_type == 'adh':
        user_last_adh_command[user_id] = time.time()
    else:
        user_last_family_command[user_id] = time.time()

def check_api_cooldown(api_type='num'):
    if api_type == 'num':
        global request_count, request_window_start, cooldown_active, cooldown_users
        current_time = time.time()
        if current_time - request_window_start >= 60:
            request_count = 0
            request_window_start = current_time
            cooldown_active = False
            cooldown_users.clear()
            return False
        if request_count >= 300:
            cooldown_active = True
            return True
        return False
    elif api_type == 'adh':
        global adh_request_count, adh_request_window_start, adh_cooldown_active, adh_cooldown_users
        current_time = time.time()
        if current_time - adh_request_window_start >= 60:
            adh_request_count = 0
            adh_request_window_start = current_time
            adh_cooldown_active = False
            adh_cooldown_users.clear()
            return False
        if adh_request_count >= 300:
            adh_cooldown_active = True
            return True
        return False
    else:
        global family_request_count, family_request_window_start, family_cooldown_active, family_cooldown_users
        current_time = time.time()
        if current_time - family_request_window_start >= 60:
            family_request_count = 0
            family_request_window_start = current_time
            family_cooldown_active = False
            family_cooldown_users.clear()
            return False
        if family_request_count >= 300:
            family_cooldown_active = True
            return True
        return False

def increment_request_count(api_type='num'):
    global request_count, adh_request_count, family_request_count
    if api_type == 'num':
        request_count += 1
    elif api_type == 'adh':
        adh_request_count += 1
    else:
        family_request_count += 1

async def send_verification_message(event):
    photo_url = PHOTO_URL
    caption = "**I'm Num Info Bot 📡 With Unlimited Free Searches 🚀** \n\n⚠️ **Join All Channels To Use The Bot**"
    buttons = [
        [Button.url("📢 Channel 1", VERIFY_LINK_1), Button.url("📢 Channel 2", VERIFY_LINK_2)],
        [Button.inline("✅ Verify Membership", b"verify_member")]
    ]
    
    try:
        msg = await event.reply(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
        return msg
    except:
        msg = await event.reply(caption, buttons=buttons, parse_mode='markdown')
        return msg

async def send_welcome_message(event):
    photo_url = PHOTO_URL
    caption = "**I'm Num Info Bot 📡 With Unlimited Free Searches 🚀**\n\n⚙️ **My Commands:**\n\n/num - **Get Number Info 📱**\n/adh - **Get Aadhar Info 🆔**\n/family - **Get Family Members Name 👨‍👩‍👧‍👦**\n/protectnum - **Protect Your Num Info 🔒**\n/protectadh - **Protect Your Aadhar Info 🔒**\n/removenum - **Remove From Secure List 🔓**\n/removeadh - Remove Aadhar From Secure List 🔓\n/prolist - **See Your Protected Data 📓**"
    
    buttons = [
        [Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", current_ch_link)]
    ]
    
    try:
        await event.reply(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
    except:
        await event.reply(caption, buttons=buttons, parse_mode='markdown')

async def check_membership(user_id):
    if is_admin(user_id):
        return True
    
    try:
        ch1_status = False
        ch2_status = False
        
        try:
            permissions = await client.get_permissions(VERIFY_CHANNEL_1, user_id)
            if permissions and hasattr(permissions, 'is_member'):
                ch1_status = permissions.is_member
            elif permissions:
                ch1_status = True
        except Exception:
            ch1_status = False
        
        try:
            permissions = await client.get_permissions(VERIFY_CHANNEL_2, user_id)
            if permissions and hasattr(permissions, 'is_member'):
                ch2_status = permissions.is_member
            elif permissions:
                ch2_status = True
        except Exception:
            ch2_status = False
        
        return ch1_status and ch2_status
        
    except Exception:
        return False

def format_number_data(data, num):
    try:
        if "Success" not in data:
            return None
        
        if "Failed" in data.get("Success", "") or data.get("Success") == "False ❌" or data.get("Success") == "Failed ❌":
            return None
        
        result_keys = [key for key in data.keys() if key.startswith("Result")]
        if not result_keys:
            return None
        
        formatted_text = "```Data\n\n"
        formatted_text += f"📡 Query : {num}\n"
        formatted_text += f"✅ Success : {data.get('Success', 'True')}\n\n"
        
        for i, key in enumerate(result_keys, 1):
            result = data[key]
            if isinstance(result, dict):
                formatted_text += f"📄 Result #{i}\n"
                formatted_text += f"📱 Number : {result.get('Number', 'N/A')}\n"
                formatted_text += f"👤 Name : {result.get('Name', 'N/A')}\n"
                father_name = result.get("Father's Name", 'N/A')
                formatted_text += f"🧔🏻 Father's Name : {father_name}\n"
                formatted_text += f"📞 Alternative Number : {result.get('Alternative Number', 'N/A')}\n"
                formatted_text += f"🆔 Adhaar Card Number : {result.get('Adhaar Card Number', 'N/A')}\n"
                formatted_text += f"🏙️ Circle : {result.get('Circle', 'N/A')}\n"
                formatted_text += f"🏠 Address : {result.get('Address', 'N/A')}\n"
                formatted_text += f"📧 Email : {result.get('Email', 'N/A')}\n"
                
                if i < len(result_keys):
                    formatted_text += "\n"
            else:
                formatted_text += f"📄 Result #{i}: {result}\n"
        
        formatted_text += "```"
        return formatted_text
    except Exception as e:
        print(f"Error formatting number data: {e}")
        return None

def format_family_data(data, aadhar):
    try:
        if not data.get("success") or not data.get("details"):
            return None
        
        details = data["details"]
        card_info = details.get("card_info", {})
        members = details.get("members", [])
        
        if not members:
            return None
        
        formatted_text = "```Family Data 👨‍👩‍👧‍👦\n\n"
        formatted_text += f"🆔 Query : {aadhar}\n"
        
        address = card_info.get('Address', 'null')
        if not address or address.strip() == "":
            address = "null"
        formatted_text += f"🏠 Address : {address}\n"
        formatted_text += f"🌇 District : {card_info.get('District', 'null')}\n"
        formatted_text += f"🏙️ State : {card_info.get('State', 'null')}\n\n"
        
        all_members = []
        
        for member in members:
            relationship = member.get("relationship", "").upper()
            name = member.get("member_name", "Unknown").strip()
            gender = member.get("gender", "")
            all_members.append({
                "name": name,
                "relationship": relationship,
                "gender": gender
            })
        
        self_members = [m for m in all_members if m["relationship"] == "SELF"]
        wife_members = [m for m in all_members if m["relationship"] == "WIFE"]
        husband_members = [m for m in all_members if m["relationship"] == "HUSBAND"]
        mother_members = [m for m in all_members if m["relationship"] == "MOTHER"]
        father_members = [m for m in all_members if m["relationship"] == "FATHER"]
        son_members = [m for m in all_members if "SON" in m["relationship"] and "GRAND" not in m["relationship"]]
        daughter_members = [m for m in all_members if "DAUGHTER" in m["relationship"] and "GRAND" not in m["relationship"]]
        grandson_members = [m for m in all_members if "GRAND SON" in m["relationship"]]
        granddaughter_members = [m for m in all_members if "GRAND DAUGHTER" in m["relationship"]]
        brother_members = [m for m in all_members if "BROTHER" in m["relationship"]]
        sister_members = [m for m in all_members if "SISTER" in m["relationship"]]
        other_members = [m for m in all_members if m["relationship"] not in ["SELF", "WIFE", "HUSBAND", "MOTHER", "FATHER", "SON", "DAUGHTER", "GRAND SON", "GRAND DAUGHTER", "BROTHER", "SISTER"]]
        
        for self_m in self_members:
            formatted_text += f"👤 Self : {self_m['name']}\n"
        
        for mother in mother_members:
            formatted_text += f"👩🏻 Mother : {mother['name']}\n"
        
        for father in father_members:
            formatted_text += f"🧔🏻 Father : {father['name']}\n"
        
        for wife in wife_members:
            formatted_text += f"👩🏻 Wife : {wife['name']}\n"
        
        for husband in husband_members:
            formatted_text += f"🧔🏻‍♂️ Husband : {husband['name']}\n"
        
        for i, son in enumerate(son_members, 1):
            suffix = f" #{i}" if len(son_members) > 1 else ""
            formatted_text += f"🧑🏻 Son{suffix} : {son['name']}\n"
        
        for i, daughter in enumerate(daughter_members, 1):
            suffix = f" #{i}" if len(daughter_members) > 1 else ""
            formatted_text += f"👩🏻 Daughter{suffix} : {daughter['name']}\n"
        
        for i, grandson in enumerate(grandson_members, 1):
            suffix = f" #{i}" if len(grandson_members) > 1 else ""
            formatted_text += f"👦🏻 Grandson{suffix} : {grandson['name']}\n"
        
        for i, granddaughter in enumerate(granddaughter_members, 1):
            suffix = f" #{i}" if len(granddaughter_members) > 1 else ""
            formatted_text += f"👧🏻 Granddaughter{suffix} : {granddaughter['name']}\n"
        
        for i, brother in enumerate(brother_members, 1):
            suffix = f" #{i}" if len(brother_members) > 1 else ""
            formatted_text += f"👨🏻 Brother{suffix} : {brother['name']}\n"
        
        for i, sister in enumerate(sister_members, 1):
            suffix = f" #{i}" if len(sister_members) > 1 else ""
            formatted_text += f"👩🏻 Sister{suffix} : {sister['name']}\n"
        
        for other in other_members:
            rel_display = other['relationship'].title()
            formatted_text += f"👤 {rel_display} : {other['name']}\n"
        
        formatted_text += "```"
        return formatted_text
    except Exception as e:
        print(f"Error formatting family data: {e}")
        return None

async def process_number(event, num):
    client = event.client
    message = event
    user_id = message.sender_id
    
    if api_locks["num"] and not is_admin(user_id):
        await message.reply("🔧 **Number Info API is Under Maintenance**\n\n📡 **You Can Still Use :**\n• /adh - **Aadhar Information**\n• /family - **Family Members Name**\n\n⚡ **Api On Hote Hee Bot Msg Bhej Dega.**", parse_mode='markdown')
        return
    
    try:
        for uid, nums in protected_numbers.items():
            if uid != user_id and num in nums:
                msg = await message.reply("🔍 Fetching data...")
                await asyncio.sleep(2)
                
                fake_data = {
                    "API BY": "@SpideyStuff 🕸️",
                    "Success": "Failed ❌",
                    "Result": f"No Information Found For {num}"
                }
                
                formatted = json.dumps(fake_data, indent=4, ensure_ascii=False)
                await msg.edit(f"```{formatted}```")
                
                if not is_admin(user_id):
                    notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                    asyncio.create_task(delete_message_later(msg, 59))
                    asyncio.create_task(delete_message_later(notice, 59))
                return
        
        if check_api_cooldown('num') and not is_admin(user_id):
            await message.reply("❄️ **API Cooldown Activated ! Just Wait 2 Minutes ❄️**", parse_mode='markdown')
            return
        
        increment_request_count('num')
        
        msg = await message.reply("🔍 Fetching data...")

        response = requests.get(NUM_API.format(num), timeout=15)

        if response.status_code != 200:
            return await msg.edit("❌ API Error!")

        raw_data = response.text

        try:
            data = response.json()
            formatted = json.dumps(data, indent=4, ensure_ascii=False)
        except:
            formatted = raw_data

        if is_admin(user_id):
            if len(formatted) < 3500:
                await msg.edit(f"```{formatted}```")
                data_msg = msg
            else:
                ist = timezone(timedelta(hours=5, minutes=30))
                now = datetime.now(ist).strftime("%H%M")
                filename = f"num_{now}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(formatted)
                await msg.delete()
                data_msg = await client.send_file(
                    message.chat_id,
                    filename,
                    caption=f"📄 Data for `{num}`"
                )
                os.remove(filename)
        else:
            formatted_text = format_number_data(data, num)
            if formatted_text:
                if len(formatted_text) < 3500:
                    await msg.edit(formatted_text)
                    data_msg = msg
                else:
                    ist = timezone(timedelta(hours=5, minutes=30))
                    now = datetime.now(ist).strftime("%H%M")
                    filename = f"{num}_{now}.txt"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(formatted_text)
                    await msg.delete()
                    data_msg = await client.send_file(
                        message.chat_id,
                        filename,
                        caption=f"📄 Data for `{num}`"
                    )
                    os.remove(filename)
            else:
                if len(formatted) < 3500:
                    await msg.edit(f"```{formatted}```")
                    data_msg = msg
                else:
                    filename = f"{num}_{int(time.time())}.txt"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(formatted)
                    await msg.delete()
                    data_msg = await client.send_file(
                        message.chat_id,
                        filename,
                        caption=f"📄 Data for `{num}`"
                    )
                    os.remove(filename)

        if not is_admin(user_id):
            notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
            asyncio.create_task(delete_message_later(data_msg, 59))
            asyncio.create_task(delete_message_later(notice, 59))

    except Exception as e:
        print(f"Error in process_number: {traceback.format_exc()}")
        await message.reply("❌ Error")

async def process_aadhar(event, adh):
    client = event.client
    message = event
    user_id = message.sender_id
    
    if api_locks["adh"] and not is_admin(user_id):
        await message.reply("🔧 **Aadhar API is Under Maintenance**\n\n📡 **You can still use:**\n• /num - **Number Information**\n• /family - **Family Members Name**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
        return
    
    try:
        for uid, aadhars in protected_aadhars.items():
            if uid != user_id and adh in aadhars:
                msg = await message.reply("🔍 Fetching data...")
                await asyncio.sleep(2)
                
                fake_data = {
                    "API BY": "SpideyStuff 🕸️",
                    "Success": "False ❌",
                    "Type": "Aadhar Info 🆔",
                    "Results": f"No Information Found For {adh}"
                }
                
                formatted = json.dumps(fake_data, indent=4, ensure_ascii=False)
                await msg.edit(f"```{formatted}```")
                
                if not is_admin(user_id):
                    notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                    asyncio.create_task(delete_message_later(msg, 59))
                    asyncio.create_task(delete_message_later(notice, 59))
                return
        
        if check_api_cooldown('adh') and not is_admin(user_id):
            await message.reply("❄️ **API Cooldown Activated ! Just Wait 2 Minutes ❄️**", parse_mode='markdown')
            return
        
        increment_request_count('adh')
        
        msg = await message.reply("🔍 Fetching Aadhar data...")

        response = requests.get(aadhar_API.format(adh), timeout=15)

        if response.status_code != 200:
            return await msg.edit("❌ API Error!")

        raw_data = response.text

        try:
            data = response.json()
            formatted = json.dumps(data, indent=4, ensure_ascii=False)
        except:
            formatted = raw_data

        if len(formatted) < 3500:
            await msg.edit(f"```{formatted}```")
            data_msg = msg
        else:
            ist = timezone(timedelta(hours=5, minutes=30))
            now = datetime.now(ist).strftime("%H%M")
            filename = f"{adh}_{now}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(formatted)
            await msg.delete()
            data_msg = await client.send_file(
                message.chat_id,
                filename,
                caption=f"📄 Aadhar data for `{adh}`"
            )
            os.remove(filename)

        if not is_admin(user_id):
            notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
            asyncio.create_task(delete_message_later(data_msg, 59))
            asyncio.create_task(delete_message_later(notice, 59))

    except Exception as e:
        print(f"Error in process_Aadhar: {traceback.format_exc()}")
        await message.reply("❌ Error")

async def process_family(event, aadhar):
    client = event.client
    message = event
    user_id = message.sender_id
    
    if api_locks["family"] and not is_admin(user_id):
        await message.reply("🔧 **Family Data API is Under Maintenance**\n\n📡 **You can still use :**\n• /num - **Number Information**\n• /adh - **Aadhar Information**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
        return
    
    try:
        for uid, aadhars in protected_aadhars.items():
            if uid != user_id and aadhar in aadhars:
                msg = await message.reply("🔍 Fetching family data...")
                await asyncio.sleep(3)
                await msg.edit("❌ **Family Data Not Found !** 📡", parse_mode='markdown')
                
                if not is_admin(user_id):
                    notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                    asyncio.create_task(delete_message_later(msg, 59))
                    asyncio.create_task(delete_message_later(notice, 59))
                return
        
        if check_api_cooldown('family') and not is_admin(user_id):
            await message.reply("❄️ **API Cooldown Activated ! Just Wait 2 Minutes ❄️**", parse_mode='markdown')
            return
        
        increment_request_count('family')
        
        msg = await message.reply("🔍 Fetching family data...")

        response = requests.get(FAMILY_API.format(aadhar), timeout=25)

        if response.status_code != 200:
            await msg.edit("❌ **Family Data Not Found !**", parse_mode='markdown')
            data_msg = msg
            if not is_admin(user_id):
                notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                asyncio.create_task(delete_message_later(data_msg, 59))
                asyncio.create_task(delete_message_later(notice, 59))
            return

        try:
            data = response.json()
            
            if not data.get("success") or not data.get("details"):
                await msg.edit("❌ **Family Data Not Found !**", parse_mode='markdown')
                data_msg = msg
                if not is_admin(user_id):
                    notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                    asyncio.create_task(delete_message_later(data_msg, 59))
                    asyncio.create_task(delete_message_later(notice, 59))
                return
            
            formatted_text = format_family_data(data, aadhar)
            
            if formatted_text:
                if len(formatted_text) < 3500:
                    await msg.edit(formatted_text)
                    data_msg = msg
                else:
                    ist = timezone(timedelta(hours=5, minutes=30))
                    now = datetime.now(ist).strftime("%H%M")
                    filename = f"family_{aadhar}_{now}.txt"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(formatted_text)
                    await msg.delete()
                    data_msg = await client.send_file(
                        message.chat_id,
                        filename,
                        caption=f"📄 Family data for Aadhar `{Aadhar}`"
                    )
                    os.remove(filename)
            else:
                await msg.edit("❌ **Family Data Not Found !**", parse_mode='markdown')
                data_msg = msg
            
            if not is_admin(user_id):
                notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                asyncio.create_task(delete_message_later(data_msg, 59))
                asyncio.create_task(delete_message_later(notice, 59))

        except Exception as e:
            await msg.edit("❌ **Family Data Not Found !**", parse_mode='markdown')
            data_msg = msg
            if not is_admin(user_id):
                notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                asyncio.create_task(delete_message_later(data_msg, 59))
                asyncio.create_task(delete_message_later(notice, 59))

    except requests.exceptions.Timeout:
        await message.reply("❌ **Family Data Not Found !**\n\n📡 The request took too long. Please try again.", parse_mode='markdown')
    except Exception as e:
        print(f"Error in process_family: {traceback.format_exc()}")
        await message.reply("❌ **Family Data Not Found !**", parse_mode='markdown')

client = TelegramClient('SpN13mAdhBot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern=r'^/start$'))
async def start_command(event):
    user_id = event.sender_id
    add_user(user_id)
    is_member = await check_membership(user_id)
    
    if is_member:
        await send_welcome_message(event)
    else:
        await send_verification_message(event)

@client.on(events.NewMessage(pattern=r'^/num'))
async def num_command(event):
    user_id = event.sender_id
    add_user(user_id)
    
    if all(api_locks.values()) and not is_admin(user_id):
        await event.reply("🔒 **All APIs are Locked By Spidey** 🕸️\n\n📡 **APIs Activate Hote Hee Bot Tujhe Msg Bhej Dega** ⚡", parse_mode='markdown')
        return
    
    if api_locks["num"] and not is_admin(user_id):
        await event.reply("🔧 **Number Info API is Under Maintenance**\n\n📡 **You can still use:**\n• /adh - **Aadhar Information**\n• /family - **Family Members Name**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
        return

    rate_ok, wait_time = check_rate_limit(user_id, 'num')
    if not rate_ok:
        msg = await event.reply(
            f"⏰ **Wait {wait_time} Seconds To Search Another Number**",
            parse_mode='markdown'
        )
        asyncio.create_task(delete_message_later(msg, wait_time))
        return

    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return

    parts = event.text.split()

    if len(parts) > 1:
        update_rate_limit(user_id, 'num')
        await process_number(event, parts[1])
    else:
        user_state[user_id] = {"type": "waiting_num", "attempts": 0}
        msg = await event.reply(
            "📱 **Send Phone Number**",
            parse_mode='markdown'
        )
        user_waiting_messages[user_id] = [msg]
        asyncio.create_task(delete_message_later(msg, 50))

        await asyncio.sleep(50)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_num":
            del user_state[user_id]
            await delete_user_messages(user_id)
            await event.reply(
                f"⏰ **{event.sender.first_name} Timeout !** Send `/num` Command Again With Number",
                parse_mode='markdown'
            )

@client.on(events.NewMessage(pattern=r'^/adh'))
async def adh_command(event):
    user_id = event.sender_id
    add_user(user_id)
    
    # Check if all APIs are locked
    if all(api_locks.values()) and not is_admin(user_id):
        await event.reply("🔒 **All APIs are Locked By Spidey** 🕸️\n\n📡 **APIs Activate Hote Hee Bot Tujhe Msg Bhej Dega** ⚡", parse_mode='markdown')
        return
    
    if api_locks["adh"] and not is_admin(user_id):
        await event.reply("🔧 **Aadhar API is Under Maintenance**\n\n📡 **You can still use:**\n• /num - **Number Information**\n• /family - **Family Members Name**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
        return

    rate_ok, wait_time = check_rate_limit(user_id, 'adh')
    if not rate_ok:
        msg = await event.reply(
            f"⏰ **Wait {wait_time} Seconds To Search Another Aadhar**",
            parse_mode='markdown'
        )
        asyncio.create_task(delete_message_later(msg, wait_time))
        return

    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return

    parts = event.text.split()

    if len(parts) > 1:
        update_rate_limit(user_id, 'adh')
        await process_aadhar(event, parts[1])
    else:
        user_state[user_id] = {"type": "waiting_adh", "attempts": 0}
        msg = await event.reply(
            "🆔 **Send Aadhar Number (12 Digits)**",
            parse_mode='markdown'
        )
        user_waiting_messages[user_id] = [msg]
        asyncio.create_task(delete_message_later(msg, 50))

        await asyncio.sleep(50)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_adh":
            del user_state[user_id]
            await delete_user_messages(user_id)
            await event.reply(
                f"⏰ **{event.sender.first_name} Timeout !** Send `/adh` Command Again With Aadhar Number",
                parse_mode='markdown'
            )

@client.on(events.NewMessage(pattern=r'^/family'))
async def family_command(event):
    user_id = event.sender_id
    add_user(user_id)
    
    if all(api_locks.values()) and not is_admin(user_id):
        await event.reply("🔒 **All APIs are Locked By Spidey** 🕸️\n\n📡 **APIs Activate Hote Hee Bot Tujhe Msg Bhej Dega** ⚡", parse_mode='markdown')
        return
    
    if api_locks["family"] and not is_admin(user_id):
        await event.reply("🔧 **Family Data API is Under Maintenance**\n\n📡 **You can still use :**\n• /num - **Number Information**\n• /adh - **Aadhar Information**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
        return

    rate_ok, wait_time = check_rate_limit(user_id, 'family')
    if not rate_ok:
        msg = await event.reply(
            f"⏰ **Wait {wait_time} Seconds To Search Another Family Data**",
            parse_mode='markdown'
        )
        asyncio.create_task(delete_message_later(msg, wait_time))
        return

    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return

    parts = event.text.split()

    if len(parts) > 1:
        aadhar = extract_aadhar(parts[1])
        if aadhar:
            update_rate_limit(user_id, 'family')
            await process_family(event, aadhar)
        else:
            await event.reply("❌ **Invalid Aadhar number! Send 12-digit Aadhar**", parse_mode='markdown')
    else:
        user_state[user_id] = {"type": "waiting_family", "attempts": 0}
        msg = await event.reply(
            "🆔 **Send Aadhar Number (12 Digits) For Family Data**",
            parse_mode='markdown'
        )
        user_waiting_messages[user_id] = [msg]
        asyncio.create_task(delete_message_later(msg, 50))

        await asyncio.sleep(50)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_family":
            del user_state[user_id]
            await delete_user_messages(user_id)
            await event.reply(
                f"⏰ **{event.sender.first_name} Timeout !** Send `/family` Command Again With Aadhar Number",
                parse_mode='markdown'
            )

@client.on(events.NewMessage(pattern=r'^/(?:lock|unlock)', func=lambda e: is_admin(e.sender_id)))
async def lock_command(event):
    global api_locks
    parts = event.text.split()
    
    if len(parts) < 2:
        await event.reply("`/lock num` — `/lock adh` — `/lock family` — `/lock all` \n\n`/unlock num` — `/unlock adh` — `/unlock family` — `/unlock all`", parse_mode='markdown')
        return
    
    command = parts[0].replace('/', '')
    target = parts[1].lower()
    
    if command == "lock":
        if target == "all":
            api_locks["num"] = True
            api_locks["adh"] = True
            api_locks["family"] = True
            await event.reply("🔒 **All APIs Are Locked by Spidey!**\n\n🔒 **Locked Successfully 🔒✅**\n\n⚡ `/unlock all`", parse_mode='markdown')
        elif target in api_locks:
            api_locks[target] = True
            api_names = {"num": "Number Info", "adh": "Aadhar Info", "family": "Family Data"}
            await event.reply(f"🔒 **{api_names[target]} API Has Been Locked Successfully!**\n\n⚡ Use `/unlock {target}`", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Option!** Use: num, adh, family, or all", parse_mode='markdown')
    
    elif command == "unlock":
        if target == "all":
            api_locks["num"] = False
            api_locks["adh"] = False
            api_locks["family"] = False
            await event.reply("🔓 **All APIs Have Been Unlocked Successfully!**\n\n✅ All search services are now available for everyone.\n\n📡 Enjoy unlimited free searches! 🚀", parse_mode='markdown')
        elif target in api_locks:
            api_locks[target] = False
            api_names = {"num": "Number Info", "adh": "Aadhar Info", "family": "Family Data"}
            await event.reply(f"🔓 **{api_names[target]} API Has Been Unlocked Successfully!**\n\n✅ The service is now available for all users.\n\n📡 Search without any restrictions! 🚀", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Option!** Use: num, adh, family, or all", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/protectnum'))
async def protectnum_command(event):
    user_id = event.sender_id
    
    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return
    
    if user_id in user_state and user_state[user_id].get("type") == "waiting_protect":
        num = extract_number(event.text)
        if num:
            if num not in protected_numbers[user_id]:
                protected_numbers[user_id].append(num)
                await event.reply(f"✅ **Number `{num}` Protected Successfully** 🔒\n\n⚠️ Your number is added in memory protected list. When bot restarts, you need to protect again!", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Number `{num}` Already In Your Protected List**", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Number! Send 10-digit number**", parse_mode='markdown')
        del user_state[user_id]
        await delete_user_messages(user_id)
        return
    
    parts = event.text.split()
    if len(parts) > 1:
        num = extract_number(parts[1])
        if num:
            if num not in protected_numbers[user_id]:
                protected_numbers[user_id].append(num)
                await event.reply(f"✅ **Number** `{num}` **Protected Successfully** 🔒\n\n⚠️ Your number is added in memory protected list. When bot restarts, you need to protect again!", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Number** `{num}` **Already In Your Protected List**", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Number! Send 10-digit number**", parse_mode='markdown')
    else:
        user_state[user_id] = {"type": "waiting_protect"}
        msg = await event.reply("🔒 **Send Number To Protect**", parse_mode='markdown')
        user_waiting_messages[user_id] = [msg]
        asyncio.create_task(delete_message_later(msg, 50))
        await asyncio.sleep(50)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_protect":
            del user_state[user_id]
            await delete_user_messages(user_id)

@client.on(events.NewMessage(pattern=r'^/protectadh'))
async def protectadh_command(event):
    user_id = event.sender_id
    
    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return
    
    if user_id in user_state and user_state[user_id].get("type") == "waiting_protectadh":
        adh = extract_aadhar(event.text)
        if adh:
            if adh not in protected_aadhars[user_id]:
                protected_aadhars[user_id].append(adh)
                await event.reply(f"✅ **Aadhar `{adh}` Protected Successfully** 🔒\n\n⚠️ Your Aadhar is added in memory protected list. When bot restarts, you need to protect again!", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Aadhar `{adh}` Already In Your Protected List**", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Aadhar! Send 12-digit number**", parse_mode='markdown')
        del user_state[user_id]
        await delete_user_messages(user_id)
        return
    
    parts = event.text.split()
    if len(parts) > 1:
        adh = extract_aadhar(parts[1])
        if adh:
            if adh not in protected_aadhars[user_id]:
                protected_aadhars[user_id].append(adh)
                await event.reply(f"✅ **Aadhar** `{adh}` **Protected Successfully** 🔒\n\n⚠️ Your Aadhar is added in memory protected list. When bot restarts, you need to protect again!", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Aadhar** `{adh}` **Already In Your Protected List**", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Aadhar! Send 12-digit number**", parse_mode='markdown')
    else:
        user_state[user_id] = {"type": "waiting_protectadh"}
        msg = await event.reply("🔒 **Send Aadhar Number To Protect**", parse_mode='markdown')
        user_waiting_messages[user_id] = [msg]
        asyncio.create_task(delete_message_later(msg, 50))
        await asyncio.sleep(50)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_protectadh":
            del user_state[user_id]
            await delete_user_messages(user_id)

@client.on(events.NewMessage(pattern=r'^/prolist'))
async def prolist_command(event):
    user_id = event.sender_id
    
    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return
    
    numbers = protected_numbers.get(user_id, [])
    aadhars = protected_aadhars.get(user_id, [])
    
    num_text = ", ".join([f"`{n}`" for n in numbers]) if numbers else "`0`"
    adh_text = ", ".join([f"`{a}`" for a in aadhars]) if aadhars else "`0`"
    
    text = f"🔒 **Your Protected Data**\n\n📞 **Numbers:** {num_text}\n🆔 **Aadhar:** {adh_text}\n\n⚠️ Remove Number : `/removenum 9876543210`\n⚠️ Remove Aadhar : `/removeadh 123456789012`"
    
    await event.reply(text, parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/removenum'))
async def removenum_command(event):
    user_id = event.sender_id
    
    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return
    
    parts = event.text.split()
    
    if len(parts) > 1:
        num = extract_number(parts[1])
        if num and num in protected_numbers.get(user_id, []):
            protected_numbers[user_id].remove(num)
            await event.reply(f"✅ **Number** `{num}` **Removed From Protected List** 🔓", parse_mode='markdown')
        else:
            await event.reply(f"❌ **Number** `{num}` **Not Found In Your Protected List**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/removenum 9876543210`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/removeadh'))
async def removeadh_command(event):
    user_id = event.sender_id
    
    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return
    
    parts = event.text.split()
    
    if len(parts) > 1:
        adh = extract_aadhar(parts[1])
        if adh and adh in protected_aadhars.get(user_id, []):
            protected_aadhars[user_id].remove(adh)
            await event.reply(f"✅ **Aadhar** `{adh}` **Removed From Protected List** 🔓", parse_mode='markdown')
        else:
            await event.reply(f"❌ **Aadhar** `{adh}` **Not Found In Your Protected List**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/removeadh 123456789012`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/v1', func=lambda e: is_admin(e.sender_id)))
async def update_v1_link(event):
    global VERIFY_CHANNEL_1, VERIFY_LINK_1
    parts = event.text.split(maxsplit=2)
    if len(parts) > 2:
        try:
            channel_id = int(parts[1])
            link = parts[2]
            VERIFY_CHANNEL_1 = channel_id
            VERIFY_LINK_1 = link
            await event.reply(f"✅ **Verification Channel 1 Updated Successfully**\n\nChannel ID: `{channel_id}`\nLink: {link}", parse_mode='markdown')
        except ValueError:
            await event.reply("❌ **Invalid Channel ID!** Use: `/v1 channel_id link`", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/v1 channel_id link`\n\nExample: `/v1 -1002744702833 https://t.me/channel_link`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/v2', func=lambda e: is_admin(e.sender_id)))
async def update_v2_link(event):
    global VERIFY_CHANNEL_2, VERIFY_LINK_2
    parts = event.text.split(maxsplit=2)
    if len(parts) > 2:
        try:
            channel_id = int(parts[1])
            link = parts[2]
            VERIFY_CHANNEL_2 = channel_id
            VERIFY_LINK_2 = link
            await event.reply(f"✅ **Verification Channel 2 Updated Successfully**\n\nChannel ID: `{channel_id}`\nLink: {link}", parse_mode='markdown')
        except ValueError:
            await event.reply("❌ **Invalid Channel ID!** Use: `/v2 channel_id link`", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/v2 channel_id link`\n\nExample: `/v2 -1003425131662 https://t.me/channel_link`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/gc', func=lambda e: is_admin(e.sender_id)))
async def update_gc_link(event):
    global current_gc_link
    parts = event.text.split(maxsplit=1)
    if len(parts) > 1:
        current_gc_link = parts[1]
        await event.reply("✅ **Group Link Updated Successfully**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/gc https://t.me/group_link`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/ch', func=lambda e: is_admin(e.sender_id)))
async def update_ch_link(event):
    global current_ch_link
    parts = event.text.split(maxsplit=1)
    if len(parts) > 1:
        current_ch_link = parts[1]
        await event.reply("✅ **Channel Link Updated Successfully**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/ch https://t.me/channel_link`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/broadcast$', func=lambda e: is_admin(e.sender_id)))
async def broadcast_command(event):
    global broadcast_active, broadcast_messages, broadcast_status_msg
    global broadcast_sent_count, broadcast_fail_count, broadcast_blocked_count
    global broadcast_deleted_count, broadcast_other_errors, broadcast_sent_message_ids
    
    if broadcast_active:
        await event.reply("⚠️ **Broadcast already in progress!**", parse_mode='markdown')
        return
    
    broadcast_active = True
    broadcast_messages = []
    broadcast_sent_count = 0
    broadcast_fail_count = 0
    broadcast_blocked_count = 0
    broadcast_deleted_count = 0
    broadcast_other_errors = 0
    broadcast_sent_message_ids = {}
    
    buttons = [[Button.inline("🚫 Cancel Broadcast", b"cancel_broadcast")]]
    
    broadcast_status_msg = await event.reply(
        "📤 **Broadcast Mode Activated**\n\nPlease send the content you want to broadcast to all users.",
        buttons=buttons,
        parse_mode='markdown'
    )

@client.on(events.NewMessage(func=lambda e: is_admin(e.sender_id) and broadcast_active))
async def process_broadcast_content(event):
    global broadcast_active, broadcast_messages, broadcast_status_msg
    global broadcast_sent_count, broadcast_fail_count, broadcast_blocked_count
    global broadcast_deleted_count, broadcast_other_errors, broadcast_sent_message_ids
    
    if event.text and event.text.startswith('/'):
        return
    
    broadcast_messages.append(event)
    
    await broadcast_status_msg.edit(
        f"📦 **Collected {len(broadcast_messages)} items for broadcast**\n📢 Starting broadcast to {len(users_list)} users...",
        buttons=[[Button.inline("🚫 Cancel Broadcast", b"cancel_broadcast")]],
        parse_mode='markdown'
    )
    
    total_users = len(users_list)
    is_album = len(broadcast_messages) > 1
    
    async def update_status():
        if not broadcast_active:
            return
        
        status_text = f"""
📊 **Live Broadcast Status**

📦 **Content Items:** {len(broadcast_messages)}
👥 **Total Users:** {total_users}
✅ **Successful:** {broadcast_sent_count}
❌ **Failed:** {broadcast_fail_count}
🚫 **Blocked Users:** {broadcast_blocked_count}
🗑️ **Deleted Accounts:** {broadcast_deleted_count}
⏳ **Progress:** {broadcast_sent_count + broadcast_fail_count}/{total_users}

⚠️ Click Cancel button to stop broadcast
        """
        
        try:
            await broadcast_status_msg.edit(
                status_text,
                buttons=[[Button.inline("🚫 Cancel Broadcast", b"cancel_broadcast")]],
                parse_mode='markdown'
            )
        except:
            pass
    
    await update_status()
    
    current_count = 0
    for user_id in users_list:
        if not broadcast_active:
            break
        
        current_count += 1
        try:
            if is_album and len(broadcast_messages) > 1:
                for msg in broadcast_messages:
                    await client.forward_messages(user_id, msg.id, msg.chat_id)
                broadcast_sent_count += 1
            else:
                msg = broadcast_messages[0]
                if msg.text:
                    sent_msg = await client.send_message(user_id, msg.text)
                elif msg.photo:
                    sent_msg = await client.send_file(user_id, msg.photo, caption=msg.caption)
                elif msg.document:
                    sent_msg = await client.send_file(user_id, msg.document, caption=msg.caption)
                else:
                    sent_msg = await client.forward_messages(user_id, msg.id, msg.chat_id)
                broadcast_sent_count += 1
                if sent_msg:
                    broadcast_sent_message_ids[user_id] = [sent_msg.id]
            
        except Exception as e:
            error_msg = str(e).lower()
            broadcast_fail_count += 1
            
            if "blocked" in error_msg:
                broadcast_blocked_count += 1
            elif "deactivated" in error_msg:
                broadcast_deleted_count += 1
            else:
                broadcast_other_errors += 1
        
        if current_count % 5 == 0 or current_count == total_users:
            await update_status()
        
        await asyncio.sleep(0.2)
    
    if not broadcast_active:
        delete_progress = 0
        total_to_delete = len(broadcast_sent_message_ids)
        
        for uid, msg_ids in broadcast_sent_message_ids.items():
            for msg_id in msg_ids:
                try:
                    await client.delete_messages(uid, msg_id)
                except:
                    pass
            delete_progress += 1
            
            if delete_progress % 10 == 0:
                try:
                    await broadcast_status_msg.edit(
                        f"🗑️ Deleting broadcasted messages... {delete_progress}/{total_to_delete}",
                        parse_mode='markdown'
                    )
                except:
                    pass
        
        final_text = f"""
🚫 **Broadcast Cancelled**

📊 **Partial Results:**
✅ **Sent to:** {broadcast_sent_count} users
🗑️ **Deleted from:** {delete_progress} users
⏹️ **Stopped at:** {current_count}/{total_users}

✅ **All broadcasted messages have been deleted successfully!**
        """
    else:
        success_rate = (broadcast_sent_count / total_users * 100) if total_users > 0 else 0
        final_text = f"""
🎉 **Broadcast Completed!**

📊 **Final Results:**
👥 **Total Users:** {total_users}
✅ **Successful:** {broadcast_sent_count}
❌ **Failed:** {broadcast_fail_count}
🚫 **Blocked Users:** {broadcast_blocked_count}
🗑️ **Deleted Accounts:** {broadcast_deleted_count}
⚡ **Other Errors:** {broadcast_other_errors}

📈 **Success Rate:** {success_rate:.1f}%
        """
    
    await broadcast_status_msg.edit(final_text, parse_mode='markdown')
    broadcast_active = False

@client.on(events.NewMessage(pattern=r'^/stats', func=lambda e: is_admin(e.sender_id)))
async def stats_command(event):
    total_users = get_user_count()
    total_protected = sum(len(nums) for nums in protected_numbers.values())
    total_protected_adh = sum(len(adhs) for adhs in protected_aadhars.values())
    
    current_time = time.time()
    num_reset = int(60 - (current_time - request_window_start)) if (current_time - request_window_start) < 60 else 0
    adh_reset = int(60 - (current_time - adh_request_window_start)) if (current_time - adh_request_window_start) < 60 else 0
    family_reset = int(60 - (current_time - family_request_window_start)) if (current_time - family_request_window_start) < 60 else 0
    
    await event.reply(f"🤖 **Bot Statistics**\n\n👥 **Total Users:** {total_users}\n🔒 **Protected Numbers:** {total_protected}\n🆔 **Protected Aadhars:** {total_protected_adh}\n\n📊 **API Usage (Last 60s):**\n• **Number API:** {request_count}/300 (Resets in {num_reset}s)\n• **Aadhar API:** {adh_request_count}/300 (Resets in {adh_reset}s)\n• **Family API:** {family_request_count}/300 (Resets in {family_reset}s)\n\n🔒 **API Lock Status:**\n• Number API: {'🔴 Locked' if api_locks['num'] else '🟢 Active'}\n• Aadhar API: {'🔴 Locked' if api_locks['adh'] else '🟢 Active'}\n• Family API: {'🔴 Locked' if api_locks['family'] else '🟢 Active'}", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/addadmin', func=lambda e: is_admin(e.sender_id)))
async def add_admin_command(event):
    global ADMIN_IDS
    parts = event.text.split()
    if len(parts) > 1:
        try:
            new_admin_id = int(parts[1])
            if new_admin_id not in ADMIN_IDS:
                ADMIN_IDS.append(new_admin_id)
                await event.reply(f"✅ **Admin `{new_admin_id}` Added Successfully**", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Admin `{new_admin_id}` Is Already An Admin**", parse_mode='markdown')
        except ValueError:
            await event.reply("❌ **Invalid User ID!** Use: `/addadmin 123456789`", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/addadmin user_id`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/removeadmin', func=lambda e: is_admin(e.sender_id)))
async def remove_admin_command(event):
    global ADMIN_IDS
    parts = event.text.split()
    if len(parts) > 1:
        try:
            admin_id = int(parts[1])
            if admin_id in ADMIN_IDS and len(ADMIN_IDS) > 1:
                ADMIN_IDS.remove(admin_id)
                await event.reply(f"✅ **Admin `{admin_id}` Removed Successfully**", parse_mode='markdown')
            elif admin_id in ADMIN_IDS and len(ADMIN_IDS) == 1:
                await event.reply("❌ **Cannot remove the last admin!**", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Admin `{admin_id}` Not Found**", parse_mode='markdown')
        except ValueError:
            await event.reply("❌ **Invalid User ID!** Use: `/removeadmin 123456789`", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/removeadmin user_id`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/listadmins', func=lambda e: is_admin(e.sender_id)))
async def list_admins_command(event):
    admin_list = "\n".join([f"👑 `{aid}`" for aid in ADMIN_IDS])
    await event.reply(f"**👥 Admin List:**\n\n{admin_list}", parse_mode='markdown')

@client.on(events.CallbackQuery)
async def callback_handler(event):
    global broadcast_active
    user_id = event.sender_id
    data = event.data.decode()
    
    if data == "cancel_broadcast":
        if not broadcast_active:
            await event.answer("No broadcast in progress!", alert=True)
            return
        
        broadcast_active = False
        await event.answer("Broadcast cancellation initiated...")
        
        if broadcast_status_msg:
            await broadcast_status_msg.edit(
                "🔄 **Cancelling broadcast...**\n\nPlease wait while we stop the broadcast and delete sent messages.",
                parse_mode='markdown'
            )
    
    elif data == "verify_member":
        is_member = await check_membership(user_id)
        if is_member:
            await event.delete()
            photo_url = PHOTO_URL
            caption = "**I'm Num Info Bot 📡 With Unlimited Free Searches 🚀**\n\n⚙️ **My Commands:**\n\n/num - **Get Number Info 📱**\n/adh - **Get Aadhar Info 🆔**\n/family - **Get Family Members Name 👨‍👩‍👧‍👦**\n/protectnum - **Protect Your Num Info 🔒**\n/protectadh - **Protect Your Aadhar Info 🔒**\n/removenum - **Remove From Secure List 🔓**\n/removeadh - **Remove Aadhar From Secure List 🔓**\n/prolist - **See Your Protected Data 📓**"
            buttons = [
                [Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", current_ch_link)]
            ]
            await event.respond(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
            await event.answer("✅ Verification Successful!", alert=True)
        else:
            await event.answer("❌ Join Both Channels First!", alert=True)

@client.on(events.NewMessage(func=lambda e: not e.text.startswith('/') if e.text else False))
async def private_text_handler(event):
    user_id = event.sender_id
    
    if broadcast_active and is_admin(user_id):
        return
    
    if user_id in user_state and user_state[user_id].get("type") == "waiting_num":
        add_user(user_id)
        
        if api_locks["num"] and not is_admin(user_id):
            await event.reply("🔧 **Number Info API is Under Maintenance**\n\n📡 **You can still use:**\n• /adh - **Aadhar Information**\n• /family - **Family Members Name**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            return
        
        num = extract_number(event.text)
        if not num:
            await event.reply("❌ **Invalid number ! Send a 10-digit phone number.**", parse_mode='markdown')
            return
        
        update_rate_limit(user_id, 'num')
        await process_number(event, num)
        if user_id in user_state:
            del user_state[user_id]
        await delete_user_messages(user_id)
        
    elif user_id in user_state and user_state[user_id].get("type") == "waiting_adh":
        add_user(user_id)
        
        if all(api_locks.values()) and not is_admin(user_id):
            	await event.reply("🔒 **All APIs are Locked By Spidey** 🕸️\n\n📡 **APIs Activate Hote Hee Bot Tujhe Msg Bhej Dega** ⚡", parse_mode='markdown')
            	del user_state[user_id]
            	await delete_user_messages(user_id)
            	return
        
        if api_locks["adh"] and not is_admin(user_id):
            await event.reply("🔧 **Aadhar API is Under Maintenance**\n\n📡 **You can still use:**\n• /num - **Number Information**\n• /family - **Family Members Name**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            return
        
        adh = extract_aadhar(event.text)
        if not adh:
            await event.reply("❌ **Invalid Aadhar ! Send a 12-digit Aadhar number.**", parse_mode='markdown')
            return
        
        update_rate_limit(user_id, 'adh')
        await process_aadhar(event, adh)
        if user_id in user_state:
            del user_state[user_id]
        await delete_user_messages(user_id)
    
    elif user_id in user_state and user_state[user_id].get("type") == "waiting_family":
        add_user(user_id)
        
        if api_locks["family"] and not is_admin(user_id):
            await event.reply("🔧 **Family Data API is Under Maintenance**\n\n📡 **You can still use :**\n• /num - **Number Information**\n• /adh - **Aadhar Information**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            return
        
        adh = extract_aadhar(event.text)
        if not adh:
            await event.reply("❌ **Invalid Aadhar ! Send a 12-digit Aadhar number.**", parse_mode='markdown')
            return
        
        update_rate_limit(user_id, 'family')
        await process_family(event, adh)
        if user_id in user_state:
            del user_state[user_id]
        await delete_user_messages(user_id)
        
    elif user_id in user_state and user_state[user_id].get("type") == "waiting_protect":
        add_user(user_id)
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            return
        await protectnum_command(event)
    
    elif user_id in user_state and user_state[user_id].get("type") == "waiting_protectadh":
        add_user(user_id)
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            return
        await protectadh_command(event)

async def notify_admin():
    try:
        for admin_id in ADMIN_IDS:
            await client.send_message(admin_id, "⚡ **I'm Activated** ⚡", parse_mode='markdown')
    except:
        pass

async def startup():
    await load_users_list()
    print(f"Bot Started Successfully! Users loaded: {len(users_list)}")
    print(f"Admins: {ADMIN_IDS}")
    await notify_admin()

print("At Your Service, Sir...")
client.loop.run_until_complete(startup())
client.run_until_disconnected()
