import os
os.system('pip install telethon')
os.system('pip install requests')
os.system('pip install datetime')
import requests
import time
import re
import asyncio
import json
from collections import defaultdict
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError, ChannelPrivateError, UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipant, ChannelParticipant

BOT_TOKEN = "8655956389:AAHITB8xDYmIPYDSa_dOVE4P6CZgfiR77ac"
API_ID = 6
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
ADMIN_ID = 1725301348
CONTACT_LINK = "https://t.me/Spidey"
CHANNEL_LINK = "https://t.me/+J-0a5CaeIZZiYzNl"
PHOTO_URL = "https://raw.githubusercontent.com/HloSpidey/photo/refs/heads/main/ss.jpg"
ALLOWED_GROUP_ID = -1003425131774
STORAGE_CHANNEL = -1003666940027
USERS_LIST_MSG_ID = 30
NUM_API = "https://hlospidey-7.vercel.app/api/number?num={}"

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
user_invalid_attempts = defaultdict(int)
user_waiting_messages = {}
protected_numbers = defaultdict(list)
request_count = 0
request_window_start = time.time()
cooldown_active = False
cooldown_users = set()
users_list = set()

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

def check_rate_limit(user_id):
    last_time = user_last_command[user_id]
    if time.time() - last_time < 15:
        return False, int(15 - (time.time() - last_time))
    return True, 0

def update_rate_limit(user_id):
    user_last_command[user_id] = time.time()

def check_api_cooldown():
    global request_count, request_window_start, cooldown_active
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

def increment_request_count():
    global request_count
    request_count += 1

async def send_welcome_message(event, is_member=False):
    photo_url = PHOTO_URL
    caption = "**I'm Num Info Bot With Unlimited Free Searches 📡**🚀\n ⚙️ **My Commands :** \n`/num 1122334455` - **Get Info **📱\n`protectnum 1122334455` - **Protect Your Number Info 🔒**\n`/removenum 1122334455` - **Remove Your Num From Protected List **🔓\n`/prolist` - **See Your Protected Numbers 📓**"
    
    if not is_member:
        caption += "\n\n⚠️ **Join Both Channels To Use The Bot**"
        buttons = [
            [Button.url("📢 Channel ", "https://t.me/SpideyStuff"), Button.url("📢 Backup", "https://t.me/HeyGc")],
            [Button.inline("Verify Membership ✅", b"verify_member")]
        ]
    else:
        buttons = [
            [Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", CHANNEL_LINK)]
        ]
    
    try:
        await event.reply(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
    except:
        await event.reply(caption, buttons=buttons, parse_mode='markdown')

async def check_membership(user_id):
    try:
        # Check membership in channel 1
        ch1_status = False
        ch2_status = False
        
        # Check Channel 1 (-1002644702466)
        try:
            # Use get_permissions for both channels/groups
            permissions = await client.get_permissions(VERIFY_CHANNEL_1, user_id)
            if permissions and hasattr(permissions, 'is_member'):
                ch1_status = permissions.is_member
            elif permissions:
                ch1_status = True
        except Exception as e:
            print(f"Channel 1 check error: {e}")
            ch1_status = False
        
        # Check Channel/Group 2 (-1003429231774)
        try:
            permissions = await client.get_permissions(VERIFY_CHANNEL_2, user_id)
            if permissions and hasattr(permissions, 'is_member'):
                ch2_status = permissions.is_member
            elif permissions:
                ch2_status = True
        except Exception as e:
            print(f"Channel 2 check error: {e}")
            ch2_status = False
        
        return ch1_status and ch2_status
        
    except Exception as e:
        print(f"Membership check error: {e}")
        return False

async def process_number(event, number_text):
    user_id = event.sender_id
    
    if cooldown_active:
        cooldown_users.add(user_id)
        msg = await event.reply("❄️ **Api Cooldown Activated** ❄️\nIt Helps To Prevent Api From Spam ❗\nWait 2 Minutes And Use Me Again 🤖", parse_mode='markdown')
        asyncio.create_task(delete_message_later(msg, 59))
        return
    
    rate_ok, wait_time = check_rate_limit(user_id)
    if not rate_ok:
        msg = await event.reply(f"⏰ **Wait {wait_time} Seconds To Search Another Number**", parse_mode='markdown')
        asyncio.create_task(delete_message_later(msg, 15))
        await asyncio.sleep(wait_time)
        await event.reply(f"👋🏻 **Hey {event.sender.first_name}** 👋🏻\nSend another number with `/num` Command, I'm ready ⚡", parse_mode='markdown')
        return
    
    num = extract_number(number_text)
    if not num:
        attempts = user_invalid_attempts[user_id] + 1
        user_invalid_attempts[user_id] = attempts
        
        if attempts >= 3:
            await delete_user_messages(user_id)
            user_invalid_attempts[user_id] = 0
            if user_id in user_state:
                del user_state[user_id]
            msg = await event.reply(f"❌ **Hey {event.sender.first_name} , Query Failed, Send Command Again With Valid Number.\n💡 `/num 1122334455`", parse_mode='markdown')
            asyncio.create_task(delete_message_later(msg, 59))
        else:
            msg = await event.reply(f"⚠️ **Invalid Number !** ({attempts}/3)\nSend 10-digit number.", parse_mode='markdown')
            if user_id not in user_waiting_messages:
                user_waiting_messages[user_id] = []
            user_waiting_messages[user_id].append(msg)
            asyncio.create_task(delete_message_later(msg, 15))
        return
    
    if user_id in user_state:
        del user_state[user_id]
    
    user_invalid_attempts[user_id] = 0
    await delete_user_messages(user_id)
    
    if num in protected_numbers.get(user_id, []):
        wait_msg = await event.reply("📡 **Fetching Info...**", parse_mode='markdown')
        await asyncio.sleep(2)
        result_text = {
            "API BY": "@SpideyStuff 🕸️",
            "Success": "Failed❗",
            "Result": f"No Information Found For {num}"
        }
        # Clean JSON to avoid emoji encoding issues
        clean_json = json.dumps(result_text, indent=2, ensure_ascii=False)
        result = f"```NUMBERㅤINFOㅤ📱📡 \n{clean_json}\n```"
        msg = await event.reply(result, parse_mode='markdown')
        copy_msg = await event.reply("⚠️ **This Data Will Get Deleted After 1 Minute** ", parse_mode='markdown')
        asyncio.create_task(delete_message_later(msg, 59))
        asyncio.create_task(delete_message_later(copy_msg, 59))
        return
    
    if check_api_cooldown():
        cooldown_users.add(user_id)
        cd_msg = await event.reply("❄️ **Api Cooldown Activated** ❄️\nIt Helps To Prevent Api From Spam/Bombing ❗\nWait 2 Minutes And Use Me Again 🤖", parse_mode='markdown')
        asyncio.create_task(delete_message_later(cd_msg, 59))
        return
    
    wait_msg = await event.reply("📡 **Fetching Info...**", parse_mode='markdown')
    
    try:
        response = requests.get(NUM_API.format(num), timeout=10)
        increment_request_count()
        data = response.json()
        
        update_rate_limit(user_id)
        
        # Clean JSON to avoid emoji/encoding issues
        clean_json = json.dumps(data, indent=2, ensure_ascii=False)
        result = f"```NUMBERㅤINFOㅤ📱📡 \n{clean_json}\n```"
        
        await wait_msg.delete()
        msg = await event.reply(result, parse_mode='markdown')
        copy_msg = await event.reply("⚠️ **This Data Will Get Deleted After 1 Minute**", parse_mode='markdown')
        asyncio.create_task(delete_message_later(msg, 59))
        asyncio.create_task(delete_message_later(copy_msg, 59))
        
    except Exception as e:
        await wait_msg.delete()
        error_msg = await event.reply("⚠️ **API Error, Please Try Again Later**", parse_mode='markdown')
        asyncio.create_task(delete_message_later(error_msg, 59))

# Initialize client
client = TelegramClient('SpideyOS7NT_Bot', API_ID, API_HASH)

# Command Handlers
@client.on(events.NewMessage(pattern=r'^/start$', func=lambda e: e.is_private))
async def start_command(event):
    user_id = event.sender_id
    add_user(user_id)
    is_member = await check_membership(user_id)
    await send_welcome_message(event, is_member)

@client.on(events.NewMessage(pattern=r'^/num'))
async def num_command(event):
    user_id = event.sender_id
    add_user(user_id)
    
    # Check membership before processing command
    is_member = await check_membership(user_id)
    if not is_member:
        await send_welcome_message(event, False)
        return
    
    parts = event.text.split()
    
    if len(parts) > 1:
        await process_number(event, parts[1])
    else:
        user_state[user_id] = {"type": "waiting_num", "attempts": 0}
        msg = await event.reply("📱 **Send Phone Number**", parse_mode='markdown')
        user_waiting_messages[user_id] = [msg]
        asyncio.create_task(delete_message_later(msg, 60))
        await asyncio.sleep(60)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_num":
            del user_state[user_id]
            await delete_user_messages(user_id)
            await event.reply(f"⏰ **{event.sender.first_name} Timeout !** Send `/num` Command Again With Number", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/protectnum'))
async def protectnum_command(event):
    user_id = event.sender_id
    
    # Check membership before processing command
    is_member = await check_membership(user_id)
    if not is_member:
        await send_welcome_message(event, False)
        return
    
    if user_id in user_state and user_state[user_id].get("type") == "waiting_protect":
        num = extract_number(event.text)
        if num:
            if num not in protected_numbers[user_id]:
                protected_numbers[user_id].append(num)
                await event.reply(f"✅ **Number {num} Protected Successfully** 🔒\n\n⚠️ Your number is added in memory protected list. When bot restarts, you need to protect again!", parse_mode='markdown')
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
        asyncio.create_task(delete_message_later(msg, 60))
        await asyncio.sleep(60)
        if user_id in user_state and user_state[user_id].get("type") == "waiting_protect":
            del user_state[user_id]
            await delete_user_messages(user_id)

@client.on(events.NewMessage(pattern=r'^/prolist'))
async def prolist_command(event):
    user_id = event.sender_id
    
    # Check membership before processing command
    is_member = await check_membership(user_id)
    if not is_member:
        await send_welcome_message(event, False)
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

@client.on(events.NewMessage(pattern=r'^/removenum'))
async def removenum_command(event):
    user_id = event.sender_id
    
    # Check membership before processing command
    is_member = await check_membership(user_id)
    if not is_member:
        await send_welcome_message(event, False)
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

@client.on(events.NewMessage(pattern=r'^/broadcast', func=lambda e: e.sender_id == ADMIN_ID))
async def broadcast_command(event):
    users = get_all_users()
    if not users:
        await event.reply("❌ **No Users Found**", parse_mode='markdown')
        return
    
    status_msg = await event.reply("📤 **Send The Message To Broadcast**\nSend /cancel to cancel", parse_mode='markdown')
    
    @client.on(events.NewMessage(chats=ADMIN_ID))
    async def broadcast_handler(broadcast_event):
        if broadcast_event.text == "/cancel":
            await status_msg.delete()
            return
        
        await status_msg.edit("🔄 **Starting Broadcast...**", parse_mode='markdown')
        success = 0
        failed = 0
        
        for uid in users:
            try:
                if broadcast_event.photo:
                    await client.send_file(uid, broadcast_event.photo, caption=broadcast_event.caption)
                elif broadcast_event.text:
                    await client.send_message(uid, broadcast_event.text)
                success += 1
            except:
                failed += 1
            await asyncio.sleep(0.2)
        
        await status_msg.edit(f"📊 **Broadcast Completed**\n✅ Success: {success}\n❌ Failed: {failed}", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/stats', func=lambda e: e.sender_id == ADMIN_ID))
async def stats_command(event):
    total_users = get_user_count()
    total_protected = sum(len(nums) for nums in protected_numbers.values())
    await event.reply(f"🤖 **Bot Statistics**\n👥 Users: {total_users}\n🔒 Protected Numbers: {total_protected}\n📊 API Requests (Last 60s): {request_count}/300", parse_mode='markdown')

@client.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    data = event.data.decode()
    
    if data == "verify_member":
        is_member = await check_membership(user_id)
        if is_member:
            photo_url = PHOTO_URL
            caption = "**I'm Num Info Bot With Unlimited Free Searches 📡**🚀\n ⚙️ **My Commands :** \n`/num 1122334455` - **Get Info **📱\n`protectnum 1122334455` - **Protect Your Number Info 🔒**\n`/removenum 1122334455` - **Remove Your Num From Protected List **🔓\n`/prolist` - **See Your Protected Numbers 📓**"
            buttons = [
                [Button.url("📞 Contact Me", CONTACT_LINK), Button.url("Channel 📢", CHANNEL_LINK)]
            ]
            await event.delete()
            await event.respond(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
            await event.answer("✅ Verification Successful !", alert=True)
        else:
            await event.answer("❌ Join Both Channels First !", alert=True)

@client.on(events.NewMessage(func=lambda e: e.is_private))
async def private_text_handler(event):
    user_id = event.sender_id
    
    # Skip if message starts with / (commands)
    if event.text and event.text.startswith('/'):
        return
    
    # Only process if user is waiting for input
    if user_id in user_state and user_state[user_id].get("type") == "waiting_num":
        add_user(user_id)
        await process_number(event, event.text)
    elif user_id in user_state and user_state[user_id].get("type") == "waiting_protect":
        add_user(user_id)
        await protectnum_command(event)
    # Ignore all other messages

@client.on(events.NewMessage(func=lambda e: e.is_group))
async def group_handler(event):
    if event.chat_id != ALLOWED_GROUP_ID:
        user_id = event.sender_id
        photo_url = PHOTO_URL
        caption = "**👋🏻 Hi, I'm OSINT Bot 📡With Unlimited Free Searches 🚀**\n❌ **Use Me In Private Chat Or In Spidey Group Only**"
        buttons = [
            [Button.url("👥 Spidey Group", current_gc_link)]
        ]
        try:
            await event.reply(file=photo_url, message=caption, buttons=buttons, parse_mode='markdown')
        except:
            await event.reply(caption, buttons=buttons, parse_mode='markdown')
        return
    
    if event.text and event.text.startswith("/num"):
        user_id = event.sender_id
        add_user(user_id)
        is_member = await check_membership(user_id)
        if not is_member:
            await send_welcome_message(event, False)
            return
        await num_command(event)
    elif event.text and event.text.startswith("/protectnum"):
        user_id = event.sender_id
        is_member = await check_membership(user_id)
        if not is_member:
            await send_welcome_message(event, False)
            return
        await protectnum_command(event)
    elif event.text and event.text.startswith("/prolist"):
        user_id = event.sender_id
        is_member = await check_membership(user_id)
        if not is_member:
            await send_welcome_message(event, False)
            return
        await prolist_command(event)
    elif event.text and event.text.startswith("/removenum"):
        user_id = event.sender_id
        is_member = await check_membership(user_id)
        if not is_member:
            await send_welcome_message(event, False)
            return
        await removenum_command(event)
    elif event.text and event.text.startswith("/broadcast") and event.sender_id == ADMIN_ID:
        await broadcast_command(event)
    elif event.text and event.text.startswith("/stats") and event.sender_id == ADMIN_ID:
        await stats_command(event)
    elif event.text and event.text.startswith("/gc") and event.sender_id == ADMIN_ID:
        await update_gc_link(event)
    elif event.text and event.text.startswith("/ch") and event.sender_id == ADMIN_ID:
        await update_ch_link(event)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    await load_users_list()
    me = await client.get_me()
    print(f"Bot Started Successfully! @{me.username}")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())	
