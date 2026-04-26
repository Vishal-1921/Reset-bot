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
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError, ChannelPrivateError, UserNotParticipantError

BOT_TOKEN = "8655956389:AAHITB8xDYmIPYDSa_dOVE4P6CZgfiR77ac"
API_ID = 6
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
ADMIN_ID = 1725301348
CONTACT_LINK = "https://t.me/HloSpidey"
CHANNEL_LINK = "https://t.me/+J-0a5CaeIZZiYzNl"
PHOTO_URL = "https://raw.githubusercontent.com/HloSpidey/photo/refs/heads/main/ss.jpg"
STORAGE_CHANNEL = -1003666940027
USERS_LIST_MSG_ID = 30
NUM_API = "https://hlospidey-7.vercel.app/api/number?num={}"
AADHAR_API = "https://spidey-stuff.vercel.app/api/aadhar?adh={}"

# Updated verification channels
VERIFY_CHANNEL_1 = -1002744702466
VERIFY_CHANNEL_2 = -1003425131774

DEFAULT_GC_LINK = "https://t.me/+E30P3iPg-U9iODhl"
DEFAULT_CH_LINK = "https://t.me/spideystuff"

current_gc_link = DEFAULT_GC_LINK
current_ch_link = DEFAULT_CH_LINK

# Data structures
user_state = {}
user_last_command = defaultdict(float)
user_last_adh_command = defaultdict(float)  # Separate cooldown for aadhar
user_invalid_attempts = defaultdict(int)
user_waiting_messages = {}
protected_numbers = defaultdict(list)
protected_aadhaars = defaultdict(list)  # For Aadhaar protection
request_count = 0
adh_request_count = 0  # Separate counter for aadhar API
request_window_start = time.time()
adh_request_window_start = time.time()  # Separate window for aadhar
cooldown_active = False
adh_cooldown_active = False
cooldown_users = set()
adh_cooldown_users = set()
users_list = set()

# Broadcast variables
broadcast_active = False
broadcast_messages = []
broadcast_status_msg = None
broadcast_sent_count = 0
broadcast_fail_count = 0
broadcast_blocked_count = 0
broadcast_deleted_count = 0
broadcast_other_errors = 0
broadcast_sent_message_ids = {}

def add_user(user_id):
    if user_id not in users_list and user_id != ADMIN_ID:
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

def extract_aadhaar(text):
    cleaned = re.sub(r'[\s\-]', '', text)
    digits = re.findall(r"\d", cleaned)
    if len(digits) >= 12:
        aadhaar = "".join(digits)[:12]
        return aadhaar if len(aadhaar) == 12 else None
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
    if command_type == 'num':
        last_time = user_last_command[user_id]
        elapsed = time.time() - last_time
        if elapsed < 17:
            return False, int(17 - elapsed)
        return True, 0
    else:  # aadhar
        last_time = user_last_adh_command[user_id]
        elapsed = time.time() - last_time
        if elapsed < 17:
            return False, int(17 - elapsed)
        return True, 0

def update_rate_limit(user_id, command_type='num'):
    if command_type == 'num':
        user_last_command[user_id] = time.time()
    else:
        user_last_adh_command[user_id] = time.time()

def check_api_cooldown(api_type='num'):
    global request_count, adh_request_count, request_window_start, adh_request_window_start
    global cooldown_active, adh_cooldown_active
    
    if api_type == 'num':
        current_time = time.time()
        if current_time - request_window_start >= 50:
            request_count = 0
            request_window_start = current_time
            cooldown_active = False
            cooldown_users.clear()
            return False
        if request_count >= 300:
            cooldown_active = True
            return True
        return False
    else:  # aadhar
        current_time = time.time()
        if current_time - adh_request_window_start >= 50:
            adh_request_count = 0
            adh_request_window_start = current_time
            adh_cooldown_active = False
            adh_cooldown_users.clear()
            return False
        if adh_request_count >= 300:
            adh_cooldown_active = True
            return True
        return False

def increment_request_count(api_type='num'):
    global request_count, adh_request_count
    if api_type == 'num':
        request_count += 1
    else:
        adh_request_count += 1

async def send_verification_message(event):
    photo_url = PHOTO_URL
    caption = "**I'm Num Info Bot 📡 With Unlimited Free Searches 🚀** \n\n⚠️ **Join All Channels To Use The Bot**"
    buttons = [
        [Button.url("📢 Channel 1", current_ch_link), Button.url("📢 Channel 2", current_gc_link)],
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
    caption = "**I'm Num Info Bot 📡 With Unlimited Free Searches 🚀**\n\n⚙️ **My Commands:**\n\n/num - **Get Number Info 📱**\n/adh - **Get Aadhaar Info 🆔**\n/protectnum - **Protect Your Number Info 🔒**\n/protectadh - **Protect Your Aadhaar Info 🔒**\n/removenum - **Remove From Protected List 🔓**\n/removeadh - **Remove Aadhaar From Protected List 🔓**\n/prolist - **See Your Protected Numbers 📓**\n/proadhlist - **See Your Protected Aadhaars 📓**"
    
    buttons = [
        [Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", CHANNEL_LINK)]
    ]
    
    try:
        await event.reply(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
    except:
        await event.reply(caption, buttons=buttons, parse_mode='markdown')

async def check_membership(user_id):
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

async def process_number(event, num):
    client = event.client
    message = event
    user_id = message.sender_id
    
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
                
                notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                asyncio.create_task(delete_message_later(msg, 59))
                asyncio.create_task(delete_message_later(notice, 59))
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

        now = datetime.now().strftime("%H%M")
        filename = f"{num}_{now}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted)

        file_size = os.path.getsize(filename)

        if file_size < 3500:
            await msg.edit(f"```{formatted}```")
            data_msg = msg
        else:
            await msg.delete()
            data_msg = await client.send_file(
                message.chat_id,
                filename,
                caption=f"📄 Data for `{num}`"
            )

        notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')

        asyncio.create_task(delete_message_later(data_msg, 59))
        asyncio.create_task(delete_message_later(notice, 59))

        os.remove(filename)

    except Exception as e:
        print(f"Error in process_number: {traceback.format_exc()}")
        await message.reply("❌ Error")

async def process_aadhaar(event, adh):
    client = event.client
    message = event
    user_id = message.sender_id
    
    try:
        for uid, aadhaars in protected_aadhaars.items():
            if uid != user_id and adh in aadhaars:
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
                
                notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')
                asyncio.create_task(delete_message_later(msg, 59))
                asyncio.create_task(delete_message_later(notice, 59))
                return
        
        increment_request_count('adh')
        
        msg = await message.reply("🔍 Fetching Aadhaar data...")

        response = requests.get(AADHAR_API.format(adh), timeout=15)

        if response.status_code != 200:
            return await msg.edit("❌ API Error!")

        raw_data = response.text

        try:
            data = response.json()
            formatted = json.dumps(data, indent=4, ensure_ascii=False)
        except:
            formatted = raw_data

        now = datetime.now().strftime("%H%M")
        filename = f"{adh}_{now}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted)

        file_size = os.path.getsize(filename)

        if file_size < 3500:
            await msg.edit(f"```{formatted}```")
            data_msg = msg
        else:
            await msg.delete()
            data_msg = await client.send_file(
                message.chat_id,
                filename,
                caption=f"📄 Aadhaar data for `{adh}`"
            )

        notice = await message.reply("⚠️ **This data will be deleted after 1 minute ⏰**", parse_mode='markdown')

        asyncio.create_task(delete_message_later(data_msg, 59))
        asyncio.create_task(delete_message_later(notice, 59))

        os.remove(filename)

    except Exception as e:
        print(f"Error in process_aadhaar: {traceback.format_exc()}")
        await message.reply("❌ Error")

import asyncio
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

client = TelegramClient('SpNumAdhBot', API_ID, API_HASH, loop=loop)

# Command Handlers
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

    rate_ok, wait_time = check_rate_limit(user_id, 'adh')
    if not rate_ok:
        msg = await event.reply(
            f"⏰ **Wait {wait_time} Seconds To Search Another Aadhaar**",
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
        await process_aadhaar(event, parts[1])
    else:
        user_state[user_id] = {"type": "waiting_adh", "attempts": 0}
        msg = await event.reply(
            "🆔 **Send Aadhaar Number (12 Digits)**",
            parse_mode='markdown'
        )
        user_waiting_messages[user_id] = [msg]
        asyncio.create_task(delete_message_later(msg, 50))

        await asyncio.sleep(50)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_adh":
            del user_state[user_id]
            await delete_user_messages(user_id)
            await event.reply(
                f"⏰ **{event.sender.first_name} Timeout !** Send `/adh` Command Again With Aadhaar Number",
                parse_mode='markdown'
            )

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
        adh = extract_aadhaar(event.text)
        if adh:
            if adh not in protected_aadhaars[user_id]:
                protected_aadhaars[user_id].append(adh)
                await event.reply(f"✅ **Aadhaar `{adh}` Protected Successfully** 🔒\n\n⚠️ Your Aadhaar is added in memory protected list. When bot restarts, you need to protect again!", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Aadhaar `{adh}` Already In Your Protected List**", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Aadhaar! Send 12-digit number**", parse_mode='markdown')
        del user_state[user_id]
        await delete_user_messages(user_id)
        return
    
    parts = event.text.split()
    if len(parts) > 1:
        adh = extract_aadhaar(parts[1])
        if adh:
            if adh not in protected_aadhaars[user_id]:
                protected_aadhaars[user_id].append(adh)
                await event.reply(f"✅ **Aadhaar** `{adh}` **Protected Successfully** 🔒\n\n⚠️ Your Aadhaar is added in memory protected list. When bot restarts, you need to protect again!", parse_mode='markdown')
            else:
                await event.reply(f"⚠️ **Aadhaar** `{adh}` **Already In Your Protected List**", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Aadhaar! Send 12-digit number**", parse_mode='markdown')
    else:
        user_state[user_id] = {"type": "waiting_protectadh"}
        msg = await event.reply("🔒 **Send Aadhaar Number To Protect**", parse_mode='markdown')
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
    
    if user_id == ADMIN_ID:
        text = "📋 **Full Protected Numbers List**\n\n"
        for uid, numbers in protected_numbers.items():
            if numbers:
                try:
                    user = await client.get_entity(uid)
                    name = user.first_name if user else str(uid)
                except:
                    name = str(uid)
                text += f"👤 {name} (`{uid}`): {', '.join(numbers)}\n"
        await event.reply(text, parse_mode='markdown')
    else:
        numbers = protected_numbers.get(user_id, [])
        if numbers:
            text = f"🔒 **Your Protected Numbers**\n\n📞 {', '.join(numbers)}\n\n To Remove : `/removenum 9876543210`"
            await event.reply(text, parse_mode='markdown')
        else:
            await event.reply("🔒 **No Protected Numbers Found**\nUse `/protectnum 9876543210` to protect", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/proadhlist'))
async def proadhlist_command(event):
    user_id = event.sender_id
    
    is_member = await check_membership(user_id)
    if not is_member:
        await send_verification_message(event)
        return
    
    if user_id == ADMIN_ID:
        text = "📋 **Full Protected Aadhaars List**\n\n"
        for uid, aadhaars in protected_aadhaars.items():
            if aadhaars:
                try:
                    user = await client.get_entity(uid)
                    name = user.first_name if user else str(uid)
                except:
                    name = str(uid)
                text += f"👤 {name} (`{uid}`): {', '.join(aadhaars)}\n"
        await event.reply(text, parse_mode='markdown')
    else:
        aadhaars = protected_aadhaars.get(user_id, [])
        if aadhaars:
            text = f"🔒 **Your Protected Aadhaars**\n\n🆔 {', '.join(aadhaars)}\n\n To Remove : `/removeadh 123456789012`"
            await event.reply(text, parse_mode='markdown')
        else:
            await event.reply("🔒 **No Protected Aadhaars Found**\nUse `/protectadh 123456789012` to protect", parse_mode='markdown')

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
        adh = extract_aadhaar(parts[1])
        if adh and adh in protected_aadhaars.get(user_id, []):
            protected_aadhaars[user_id].remove(adh)
            await event.reply(f"✅ **Aadhaar** `{adh}` **Removed From Protected List** 🔓", parse_mode='markdown')
        else:
            await event.reply(f"❌ **Aadhaar** `{adh}` **Not Found In Your Protected List**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/removeadh 123456789012`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/gc', func=lambda e: e.sender_id == ADMIN_ID))
async def update_gc_link(event):
    global current_gc_link
    parts = event.text.split(maxsplit=1)
    if len(parts) > 1:
        current_gc_link = parts[1]
        await event.reply("✅ **Group Link Updated Successfully**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/gc https://t.me/group_link`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/ch', func=lambda e: e.sender_id == ADMIN_ID))
async def update_ch_link(event):
    global current_ch_link
    parts = event.text.split(maxsplit=1)
    if len(parts) > 1:
        current_ch_link = parts[1]
        await event.reply("✅ **Channel Link Updated Successfully**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/ch https://t.me/channel_link`", parse_mode='markdown')

# Broadcast System
@client.on(events.NewMessage(pattern=r'^/broadcast$', func=lambda e: e.sender_id == ADMIN_ID))
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

@client.on(events.NewMessage(func=lambda e: e.sender_id == ADMIN_ID and broadcast_active))
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

@client.on(events.NewMessage(pattern=r'^/stats', func=lambda e: e.sender_id == ADMIN_ID))
async def stats_command(event):
    total_users = get_user_count()
    total_protected = sum(len(nums) for nums in protected_numbers.values())
    total_protected_adh = sum(len(adhs) for adhs in protected_aadhaars.values())
    await event.reply(f"🤖 **Bot Statistics**\n👥 Users: {total_users}\n🔒 Protected Numbers: {total_protected}\n🆔 Protected Aadhaars: {total_protected_adh}\n📊 Num API Requests (Last 60s): {request_count}/300\n📊 Aadhar API Requests (Last 60s): {adh_request_count}/300", parse_mode='markdown')

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
            caption = "**I'm Num Info Bot 📡 With Unlimited Free Searches 🚀**\n\n⚙️ **My Commands:**\n\n/num - **Get Number Info 📱**\n/adh - **Get Aadhaar Info 🆔**\n/protectnum - **Protect Your Number Info 🔒**\n/protectadh - **Protect Your Aadhaar Info 🔒**\n/removenum - **Remove From Protected List 🔓**\n/removeadh - **Remove Aadhaar From Protected List 🔓**\n/prolist - **See Your Protected Numbers 📓**\n/proadhlist - **See Your Protected Aadhaars 📓**"
            buttons = [
                [Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", CHANNEL_LINK)]
            ]
            await event.respond(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
            await event.answer("✅ Verification Successful!", alert=True)
        else:
            await event.answer("❌ Join Both Channels First!", alert=True)

@client.on(events.NewMessage(func=lambda e: not e.text.startswith('/') if e.text else False))
async def private_text_handler(event):
    user_id = event.sender_id
    
    if broadcast_active:
        return
    
    if user_id in user_state and user_state[user_id].get("type") == "waiting_num":
        add_user(user_id)
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
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            return
        
        adh = extract_aadhaar(event.text)
        if not adh:
            await event.reply("❌ **Invalid Aadhaar ! Send a 12-digit Aadhaar number.**", parse_mode='markdown')
            return
        
        update_rate_limit(user_id, 'adh')
        await process_aadhaar(event, adh)
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

async def main():
    try:
        await client.start(bot_token=BOT_TOKEN)
        await load_users_list()
        me = await client.get_me()
        print(f"Bot Started Successfully! @{me.username}")

        # 🔔 ADD HERE
        try:
            await client.send_message(
                172539202,
                "⚡ Bot Activated Successfully!\n\nStatus: Online ✅"
            )
        except Exception as e:
            print(f"Failed to send startup notification: {e}")

        await client.run_until_disconnected()
        

if __name__ == "__main__":
    try:
        import asyncio
        import traceback

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(main())

    except KeyboardInterrupt:
        print("Bot stopped by user")

    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
