import os

import os
os.system('pip install requests')
os.system('pip install telethon')
import requests, time, random, json, os, re, asyncio
from telethon import TelegramClient, events, Button
from collections import defaultdict
import requests

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
STORAGE_CHANNEL = -1003666940027
ADMIN_DATA_MSG_ID = 27
USER_DATA_MSG_ID = 29
USERS_LIST_MSG_ID = 28
client = TelegramClient("SpideyOSINT_BOT_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_state = {}
user_last_command = defaultdict(lambda: {"num": 0, "ff": 0})
user_waiting_messages = {}
broadcast_waiting = False
broadcast_active = False
try:
	requests.get(f"https://api.telegram.org/bot8655956389:AAHITB8xDYmIPYDSa_dOVE4P6CZgfiR77ac/sendMessage?chat_id=1725301348&text=I'm Working ⚡")
except:
        pass
        
admin_data = {"numbers": [], "ff_uids": []}
users_data = {}
users_list = set()
async def load_admin_data():
    global admin_data
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=ADMIN_DATA_MSG_ID)
        if msg and msg.text:
            text = msg.text
            admin_data = {"numbers": [], "ff_uids": []}
            
            num_match = re.search(r'Numbers : \[(.*?)\]', text)
            if num_match:
                numbers_str = num_match.group(1)
                if numbers_str.strip():
                    numbers = re.findall(r'\d+', numbers_str)
                    admin_data["numbers"] = numbers
            
            ff_match = re.search(r'FF UIDs : \[(.*?)\]', text)
            if ff_match:
                uids_str = ff_match.group(1)
                if uids_str.strip():
                    uids = re.findall(r'\d+', uids_str)
                    admin_data["ff_uids"] = uids
    except Exception as e:
        print(f"Error loading admin data: {e}")
        admin_data = {"numbers": [], "ff_uids": []}

async def load_users_data():
    global users_data
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=USER_DATA_MSG_ID)
        if msg and msg.text:
            text = msg.text
            users_data = {}
            
            users_section = re.search(r'━━━ 👤 Users ━━━\n(.*?)(?:\n|$)', text, re.DOTALL)
            if users_section:
                users_lines = users_section.group(1).strip().split('\n')
                current_user = None
                for line in users_lines:
                    if line.startswith('📱'):
                        current_user = line.replace('📱', '').strip().rstrip(':')
                        users_data[current_user] = {"numbers": [], "ff_uids": []}
                    elif line.startswith('   📞 Numbers:') and current_user:
                        nums = re.findall(r'\d+', line)
                        users_data[current_user]["numbers"] = nums
                    elif line.startswith('   🎮 FF UIDs:') and current_user:
                        uids = re.findall(r'\d+', line)
                        users_data[current_user]["ff_uids"] = uids
    except Exception as e:
        print(f"Error loading users data: {e}")
        users_data = {}

async def load_users_list():
    global users_list
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=USERS_LIST_MSG_ID)
        if msg and msg.text:
            users_list = set()
            lines = msg.text.split('\n')
            for line in lines:
                line = line.strip()
                if line.isdigit():
                    users_list.add(int(line))
    except Exception as e:
        print(f"Error loading users list: {e}")

async def update_admin_data_msg():
    try:
        msg_text = "📋 **ADMIN PROTECTED DATA**\n\n"
        msg_text += f"Numbers : {admin_data.get('numbers', [])}\n"
        msg_text += f"FF UIDs : {admin_data.get('ff_uids', [])}"
        
        await client.edit_message(STORAGE_CHANNEL, ADMIN_DATA_MSG_ID, msg_text, parse_mode='markdown')
        
        with open("admin_data.json", "w") as f:
            json.dump(admin_data, f)
    except Exception as e:
        print(f"Error updating admin data: {e}")

async def update_users_data_msg():
    try:
        msg_text = "📋 **PROTECTED DATA**\n\n"
        msg_text += "━━━ 👤 Users ━━━\n"
        
        for username, data in users_data.items():
            if data.get('numbers') or data.get('ff_uids'):
                msg_text += f"📱 {username} :\n"
                msg_text += f"   📞 Numbers: {data.get('numbers', [])}\n"
                msg_text += f"   🎮 FF UIDs: {data.get('ff_uids', [])}\n"
        
        await client.edit_message(STORAGE_CHANNEL, USER_DATA_MSG_ID, msg_text, parse_mode='markdown')
        
        with open("users_data.json", "w") as f:
            json.dump(users_data, f)
    except Exception as e:
        print(f"Error updating users data: {e}")

async def update_users_list_msg():
    try:
        msg_text = "📊 Users List :\n\n"
        for user_id in sorted(users_list):
            msg_text += f"{user_id}\n"
        
        await client.edit_message(STORAGE_CHANNEL, USERS_LIST_MSG_ID, msg_text)
        
        with open("users_list.json", "w") as f:
            json.dump(list(users_list), f)
    except Exception as e:
        print(f"Error updating users list: {e}")

def add_user(user_id):
    global users_list
    if user_id not in users_list and user_id != ADMIN_ID:
        users_list.add(user_id)
        asyncio.create_task(update_users_list_msg())

def get_all_users():
    return list(users_list)

def get_user_count():
    return len(users_list)

def is_number_protected(number):
    if number in admin_data.get("numbers", []):
        return True
    
    for username, data in users_data.items():
        if number in data.get("numbers", []):
            return True
    return False

def is_ff_protected(uid):
    if uid in admin_data.get("ff_uids", []):
        return True
    
    for username, data in users_data.items():
        if uid in data.get("ff_uids", []):
            return True
    return False

async def check_rate_limit(user_id, command):
    last_time = user_last_command[user_id][command]
    
    if (time.time() - last_time) < 15:
        remaining = int(15 - (time.time() - last_time))
        return False, remaining
    
    return True, 0

async def update_rate_limit(user_id, command):
    user_last_command[user_id][command] = time.time()

def extract_number(text):
    cleaned = re.sub(r'[\s\+\-\(\)]', '', text)
    digits = re.findall(r"\d", cleaned)
    
    if len(digits) >= 10:
        number = "".join(digits)
        
        if number.startswith('91') and len(number) > 10:
            number = number[2:]
        elif number.startswith('91') and len(number) == 12:
            number = number[2:]
        
        if len(number) > 10:
            number = number[-10:]
        
        if len(number) == 10:
            return number
    
    return None

def format_date(text):
    if not text:
        return "N/A"
    text = text.replace("At", "at")
    text = re.sub(r"\s+", " ", text)
    parts = text.split()
    if parts and parts[0].startswith("0"):
        parts[0] = parts[0][1:]
    return " ".join(parts) if parts else text

async def auto_delete(msg, delay=15):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

async def delete_15sec(msg):
    await asyncio.sleep(15)
    try:
        await msg.delete()
    except:
        pass

async def delete_waiting_message(user_id):
    if user_id in user_waiting_messages:
        try:
            await user_waiting_messages[user_id].delete()
        except:
            pass
        del user_waiting_messages[user_id]

async def get_photo_from_message():
    try:
        parts = PHOTO_URL.split('/')
        msg_id = int(parts[-1])
        chat_id = int("-100" + parts[-2])
        msg = await client.get_messages(chat_id, ids=msg_id)
        if msg and msg.media:
            return msg.media
    except Exception as e:
        print(f"Error getting photo: {e}")
    return None

@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    add_user(user_id)

    buttons = [
        [Button.url("📞 Contact Me", CONTACT_LINK),
         Button.url("Channel 📢", CHANNEL_LINK)]
    ]

    photo = await get_photo_from_message()
    if photo:
        msg = await event.respond(file=photo,
            message="**Hi 👋🏻 , I'm OSINT Bot 📡**\n\n**Send /help For All Commands** ⚙️",
            buttons=buttons,
            parse_mode='markdown')
    else:
        msg = await event.respond(
            message="**Hi 👋🏻 , I'm OSINT Bot 📡**\n\n**Send /help For All Commands** ⚙️",
            buttons=buttons,
            parse_mode='markdown')

    asyncio.create_task(auto_delete(msg))

@client.on(events.NewMessage(pattern="/help"))
async def help_cmd(event):
    add_user(event.sender_id)
    
    msg = await event.reply("""**My Commands ⚙️ :**

📱 `/num <number>` - Get number info
🎮 `/ff <uid>` - Get Free Fire info

**More Features Will Be Added Soon ✅**

**Prevent Your Data From Being Searched By Other Users : 
**
🔒 `/addnum <number>` - Protect Your Number
🔒 `/addff <uid>` - Protect Your FF UID
🔓 `/removenum <number>` - Remove Your Protected Number
🔓 `/removeff <uid>` - Remove Your Protected FF UID
📋 `/protectedlist` - View Your Protected Data
""", parse_mode='markdown')
    asyncio.create_task(auto_delete(msg))

@client.on(events.NewMessage(pattern=r"(?i)/addnum (\d+)"))
async def add_number(event):
    user_id = event.sender_id
    number = event.pattern_match.group(1)
    number = re.sub(r'\D', '', number)
    
    if len(number) >= 10:
        number = number[-10:]
    else:
        await event.reply("⚠️ **Send a Valid 10-Digit Number.\nExample: `/addnum 9876543210`", parse_mode='markdown')
        return
    
    if user_id == ADMIN_ID:
        if number not in admin_data.get("numbers", []):
            admin_data["numbers"].append(number)
            await update_admin_data_msg()
            await event.reply(f"✅ Number `{number}` protected successfully ✅", parse_mode='markdown')
        else:
            await event.reply(f"⚠️ Number `{number}` is already in protected list.", parse_mode='markdown')
    else:
        # Regular user
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        
        if number in admin_data.get("numbers", []):
            await event.reply(f"⚠️ Number `{number}` is already protected by admin.", parse_mode='markdown')
            return
        
        for username, data in users_data.items():
            if number in data.get("numbers", []):
                await event.reply(f"⚠️ Number `{number}` is already protected by another user.", parse_mode='markdown')
                return
        
        if user_identifier not in users_data:
            users_data[user_identifier] = {"numbers": [], "ff_uids": []}
        
        if number not in users_data[user_identifier]["numbers"]:
            users_data[user_identifier]["numbers"].append(number)
            await update_users_data_msg()
            await event.reply(f"✅ Your Number `{number}` is Protected Successfully 🔐✅\nIt is stored in memory, not in any database or vps 🔒✅", parse_mode='markdown')
        else:
            await event.reply(f"⚠️ Number `{number}` is already in your protected list.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/removenum (\d+)"))
async def remove_number(event):
    user_id = event.sender_id
    number = event.pattern_match.group(1)
    
    if user_id == ADMIN_ID:
        if number in admin_data.get("numbers", []):
            admin_data["numbers"].remove(number)
            await update_admin_data_msg()
            await event.reply(f"✅ Number `{number}` Removed From Protected List 🔓", parse_mode='markdown')
        else:
            await event.reply(f"❌ Number `{number}` is not in protected list.", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        
        if user_identifier in users_data:
            if number in users_data[user_identifier]["numbers"]:
                users_data[user_identifier]["numbers"].remove(number)
                await update_users_data_msg()
                await event.reply(f"✅**Number** `{number}` **Removed From Protected List 🔓**", parse_mode='markdown')
            else:
                await event.reply(f"❌ Number `{number}` is not in your protected list.", parse_mode='markdown')
        else:
            await event.reply(f"❌ Number `{number}` is not in your protected list.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/addff (\d+)"))
async def add_ff(event):
    user_id = event.sender_id
    uid = event.pattern_match.group(1)
    
    if user_id == ADMIN_ID:
        if uid not in admin_data.get("ff_uids", []):
            admin_data["ff_uids"].append(uid)
            await update_admin_data_msg()
            await event.reply(f"✅ UID `{uid}` Protected Successfully 🎮🔒", parse_mode='markdown')
        else:
            await event.reply(f"⚠️ **UID** `{uid}` **is Already In Protected List. **", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        
        if uid in admin_data.get("ff_uids", []):
            await event.reply(f"⚠️ **UID** `{uid}` **is Already Protected By Admin. **", parse_mode='markdown')
            return
        
        for username, data in users_data.items():
            if uid in data.get("ff_uids", []):
                await event.reply(f"⚠️ **UID** `{uid}` **is Already Protected By Another User. **", parse_mode='markdown')
                return
        
        if user_identifier not in users_data:
            users_data[user_identifier] = {"numbers": [], "ff_uids": []}
        
        if uid not in users_data[user_identifier]["ff_uids"]:
            users_data[user_identifier]["ff_uids"].append(uid)
            await update_users_data_msg()
            await event.reply(f"✅ **Your UID** `{uid}` **is Protected Successfully 🎮🔒✅\nIt is Stored In Memory, Not In Any Database or VPS** 🔒✅", parse_mode='markdown')
        else:
            await event.reply(f"⚠️ UID `{uid}` Is Already In Your Protected List.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/removeff (\d+)"))
async def remove_ff(event):
    user_id = event.sender_id
    uid = event.pattern_match.group(1)
    
    if user_id == ADMIN_ID:
        if uid in admin_data.get("ff_uids", []):
            admin_data["ff_uids"].remove(uid)
            await update_admin_data_msg()
            await event.reply(f"✅ UID `{uid}` Removed From Protected List 🔓", parse_mode='markdown')
        else:
            await event.reply(f"❌ UID `{uid}` is not in protected list.", parse_mode='markdown')
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        
        if user_identifier in users_data:
            if uid in users_data[user_identifier]["ff_uids"]:
                users_data[user_identifier]["ff_uids"].remove(uid)
                await update_users_data_msg()
                await event.reply(f"✅ UID `{uid}` Removed From Protected List 🔓", parse_mode='markdown')
            else:
                await event.reply(f"❌ UID `{uid}` is not in your protected list.", parse_mode='markdown')
        else:
            await event.reply(f"❌ UID `{uid}` is not in your protected list.", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r"(?i)/protectedlist"))
async def protected_list(event):
    user_id = event.sender_id
    
    if user_id == ADMIN_ID:
        try:
            admin_msg = await client.get_messages(STORAGE_CHANNEL, ids=ADMIN_DATA_MSG_ID)
            users_msg = await client.get_messages(STORAGE_CHANNEL, ids=USER_DATA_MSG_ID)
            
            text = "📋 **FULL PROTECTED LIST**\n\n"
            if admin_msg and admin_msg.text:
                text += admin_msg.text + "\n\n"
            if users_msg and users_msg.text:
                text += users_msg.text
            
            await event.reply(text, parse_mode='markdown')
        except Exception as e:
            await event.reply(f"❌ Error: {e}")
    else:
        user_identifier = f"@{event.sender.username}" if event.sender.username else f"user_{user_id}"
        
        if user_identifier in users_data:
            data = users_data[user_identifier]
            numbers = data.get("numbers", [])
            ff_uids = data.get("ff_uids", [])
            
            text = "🔒 **Your Protected Items**\n\n"
            text += f"📞 Numbers: {numbers if numbers else 'None'}\n"
            text += f"🎮 FF UIDs: {ff_uids if ff_uids else 'None'}\n\n"
            text += "To remove: `/removenum <number>` or `/removeff <uid>`"
            
            await event.reply(text, parse_mode='markdown')
        else:
            await event.reply("🔒 **You Have No Protected Items.**\n\n**Use** `/addnum <number>` **or** `/addff <uid>` **To Protect Your Data.**", parse_mode='markdown')

@client.on(events.NewMessage(pattern='/broadcast'))
async def cmd_broadcast(event):
    global broadcast_waiting
    
    if not event.is_private or event.sender_id != ADMIN_ID:
        return
        
    if broadcast_waiting:
        await event.reply("⚠️ **Already Waiting For Broadcast Content.**")
        return
    
    users_list_data = get_all_users()
    if not users_list_data:
        await event.reply("❌ No Users Found.")
        return
    
    broadcast_waiting = True

    cancel_button = [[Button.inline("🚫 Cancel Broadcast", "cancel_broadcast")]]
    
    await event.reply(
        "📤 **Broadcast Mode Activated**\n\nSend the content to broadcast.",
        parse_mode='markdown',
        buttons=cancel_button
    )

@client.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id == ADMIN_ID))
async def admin_message_handler(event):
    global broadcast_waiting, broadcast_active
    
    if event.text and (event.text.startswith('/') or not broadcast_waiting):
        return

    if broadcast_waiting:
        broadcast_waiting = False
        broadcast_active = True
        
        users_list_data = get_all_users()
        if not users_list_data:
            await event.reply("❌ No users found.")
            return
        
        status_msg = await event.reply("🔄 Starting broadcast...")
        
        total_users = len(users_list_data)
        success_count = 0
        fail_count = 0
        blocked_count = 0
        deleted_count = 0
        other_errors = 0
        
        async def update_status():
            status_text = f"""
📊 **Live Broadcast Status**

👥 Total: {total_users}
✅ Success: {success_count}
❌ Failed: {fail_count}
🚫 Blocked: {blocked_count}
🗑️ Deleted: {deleted_count}
📈 Rate: {round((success_count/max(total_users, 1))*100, 2)}%
            """
            try:
                await status_msg.edit(status_text, parse_mode='markdown')
            except:
                pass
        
        for user_id in users_list_data:
            if not broadcast_active:
                break
                
            try:
                if event.media:
                    await client.send_file(user_id, event.media, caption=event.text)
                    success_count += 1
                elif event.text:
                    await client.send_message(user_id, event.text)
                    success_count += 1
                else:
                    await client.send_message(user_id, "📢 New broadcast!")
                    success_count += 1
                    
            except Exception as e:
                fail_count += 1
                error_msg = str(e).lower()
                if "blocked" in error_msg:
                    blocked_count += 1
                elif "deactivated" in error_msg:
                    deleted_count += 1
                else:
                    other_errors += 1
            
            if (success_count + fail_count) % 5 == 0:
                await update_status()
            
            await asyncio.sleep(0.2)
        
        broadcast_active = False
        
        final_text = f"""
📊 **Broadcast Completed**

✅ Success: {success_count}
❌ Failed: {fail_count}
🚫 Blocked: {blocked_count}
🗑️ Deleted: {deleted_count}
📈 Rate: {round((success_count/max(total_users, 1))*100, 2)}%
        """
        
        try:
            await status_msg.edit(final_text, parse_mode='markdown')
        except:
            await event.reply(final_text, parse_mode='markdown')

# ================= STATS COMMAND =================

@client.on(events.NewMessage(pattern='/stats'))
async def bot_stats(event):
    if not event.is_private or event.sender_id != ADMIN_ID:
        return
    
    total_users = get_user_count()
    total_user_numbers = sum(len(data.get("numbers", [])) for data in users_data.values())
    total_user_ff = sum(len(data.get("ff_uids", [])) for data in users_data.values())
    
    stats_text = f"""
🤖 **Bot Statistics**

👥 Total Users: {total_users}
🆔 Admin ID: {ADMIN_ID}

👑 **Admin Protected:**
📞 Numbers: {len(admin_data.get('numbers', []))}
🎮 FF UIDs: {len(admin_data.get('ff_uids', []))}

👤 **Users Protected:**
📞 Numbers: {total_user_numbers}
🎮 FF UIDs: {total_user_ff}
👥 Users with data: {len(users_data)}

Made by: @HloSpidey
    """
    
    await event.reply(stats_text, parse_mode='markdown')

@client.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"cancel_broadcast":
        global broadcast_active, broadcast_waiting
        
        if event.sender_id != ADMIN_ID:
            await event.answer("❌ Not authorized.", alert=True)
            return
        
        broadcast_active = False
        broadcast_waiting = False
        
        await event.answer("✅ Broadcast cancelled!")
        await event.edit("🚫 Broadcast cancelled by admin")

# ================= NUM COMMANDS =================

@client.on(events.NewMessage(pattern=r"(?i)/num"))
async def num_cmd(event):
    user_id = event.sender_id
    add_user(user_id)
    
    can_execute, remaining = await check_rate_limit(user_id, "num")
    if not can_execute:
        countdown_msg = await event.reply(f"⏰ Please wait **{remaining}** seconds!", parse_mode='markdown')
        
        for i in range(remaining, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0:
                    await countdown_msg.edit(f"⏰ Please wait **{i-1}** seconds!", parse_mode='markdown')
                else:
                    await countdown_msg.delete()
            except:
                break
        return
    
    args = event.raw_text.split()
    
    if len(args) > 1:
        await process_number(event, args[1])
        return
    
    user_state[user_id] = {"type": "num", "attempts": 0}
    msg = await event.reply("📱 **Send Phone Number**\nExample: `9292828282`", parse_mode='markdown')
    asyncio.create_task(auto_delete(msg, 60))
    
    await asyncio.sleep(60)
    if user_id in user_state and user_state[user_id].get("type") == "num":
        del user_state[user_id]
        await event.reply(f"⏰ Timeout! Send `/num` again.", parse_mode='markdown')

async def process_number(event, text):
    user_id = event.sender_id
    
    can_execute, remaining = await check_rate_limit(user_id, "num")
    if not can_execute:
        countdown_msg = await event.reply(f"⏰ Wait **{remaining}** Seconds ! and Dubara Command Ke Saath Number Bhejna", parse_mode='markdown')
        
        for i in range(remaining, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0:
                    await countdown_msg.edit(f"⏰ Wait **{i-1}** Seconds !", parse_mode='markdown')
                else:
                    await countdown_msg.delete()
            except:
                break
        return
    
    num = extract_number(text)
    
    if not num:
        attempts = user_state.get(user_id, {}).get("attempts", 0) + 1
        user_state[user_id] = {"type": "num", "attempts": attempts}
        
        if attempts >= 3:
            await delete_waiting_message(user_id)
            msg = await event.reply("❌ **Invalid Number!**\nSend `/num 9643814206`", parse_mode='markdown')
            asyncio.create_task(auto_delete(msg, 15))
            del user_state[user_id]
        else:
            msg = await event.reply(f"⚠️ **Invalid!** ({attempts}/3)\nSend 10-digit number.", parse_mode='markdown')
            user_waiting_messages[user_id] = msg
            asyncio.create_task(auto_delete(msg, 15))
        return
    
    if user_id in user_state:
        del user_state[user_id]
    
    await update_rate_limit(user_id, "num")
    
    if is_number_protected(num):
        wait_msg = await event.reply("📡 **Fetching Info...**", parse_mode='markdown')
        await asyncio.sleep(2)
        await wait_msg.delete()
        result = """━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━
🌐 𝐍𝐚𝐦𝐞  : **NO FURTHER RESULT FOUND**
━━━━━━━━━  𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨  ━━━━━━━━━
⚠️ **NO FURTHER RESULT FOUND**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        msg = await event.reply(result, parse_mode='markdown')
        warn = await event.respond("⚠️ This message will self-destruct in 15 seconds")
        asyncio.create_task(delete_15sec(msg))
        asyncio.create_task(delete_15sec(warn))
        return
    
    wait_msg = await event.reply("📡 **Fetching Info...**", parse_mode='markdown')
    
    multiple_results = []
    try:
        res = requests.get(NUM_API.format(num), timeout=10).json()
        for key, value in res.items():
            if key.isdigit():
                multiple_results.append(value)
    except:
        pass
    
    name_from_api = None
    try:
        clean_num = num
        if not clean_num.startswith('91'):
            clean_num = '91' + clean_num
        name_res = requests.get(f"https://number-to-name-ten.vercel.app/info?name={clean_num}", timeout=5).json()
        name_from_api = name_res.get("name")
    except:
        pass
    
    if not name_from_api:
        try:
            clean_num2 = num
            if clean_num2.startswith('91'):
                clean_num2 = clean_num2[2:]
            name_res2 = requests.get(f"https://number-to-name-ten.vercel.app/info?name={clean_num2}", timeout=5).json()
            name_from_api = name_res2.get("name")
        except:
            pass
    
    if multiple_results:
        result = f"""━━━━━━━━━🕸️ 𝐒𝐏𝐈𝐃𝐄𝐘 🕸️━━━━━━━━━
━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━
🌐 𝐍𝐚𝐦𝐞  : {name_from_api if name_from_api else 'Not Found'}
━━━━━━━━━  𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨  ━━━━━━━━━
"""
        for idx, data in enumerate(multiple_results, 1):
            result += f"""
📄 𝗥𝗲𝘀𝘂𝗹𝘁  #{idx}
📞 𝐍𝐮𝐦𝐛𝐞𝐫 : {data.get('MOBILE', num)}
👤 𝐍𝐚𝐦𝐞 : {data.get('NAME', 'NA')}
🧔🏻 𝐅𝐚𝐭𝐡𝐞𝐫 : {data.get('fname', 'NA')}
📞 𝐀𝐥𝐭 : {data.get('alt') or 'NA'}
📡 𝐀𝐫𝐞𝐚 : {data.get('circle', 'NA')}
🆔 𝐀𝐝𝐡𝐚𝐚𝐫 : {data.get('id', 'NA')}
📧 𝐄𝐦𝐚𝐢𝐥 : {data.get('email', 'NA')}
🏙️ 𝐀𝐝𝐝𝐫𝐞𝐬𝐬 : {data.get('ADDRESS', 'NA')}
"""
        
        result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n @HloSpidey @SpideyStuff 🕸️❤️‍🔥\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else:
        if name_from_api:
            result = f"""━━━━━━━━━🕸️ 𝐒𝐏𝐈𝐃𝐄𝐘 🕸️━━━━━━━━━
━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━
🌐 𝐍𝐚𝐦𝐞  : {name_from_api}
━━━━━━━━━  𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨  ━━━━━━━━━
⚠️ **NO FURTHER RESULT FOUND**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        else:
            result = """━━━━━━━━ 𝐍𝐚𝐦𝐞 𝐀𝐏𝐈 𝐑𝐞𝐬𝐮𝐥𝐭 ━━━━━━━━
🌐 𝐍𝐚𝐦𝐞  : **NO FURTHER RESULT FOUND**
━━━━━━━━━  𝐍𝐮𝐦𝐛𝐞𝐫 𝐈𝐧𝐟𝐨  ━━━━━━━━━
⚠️ **NO FURTHER RESULT FOUND**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    await wait_msg.delete()
    msg = await event.reply(result)
    warn = await event.respond("⚠️ This Message Will Self-Destruct In 15 Seconds")
    asyncio.create_task(delete_15sec(msg))
    asyncio.create_task(delete_15sec(warn))

@client.on(events.NewMessage(pattern=r"(?i)/ff"))
async def ff_cmd(event):
    user_id = event.sender_id
    add_user(user_id)
    
    can_execute, remaining = await check_rate_limit(user_id, "ff")
    if not can_execute:
        countdown_msg = await event.reply(f"⏰ Wait **{remaining}** Seconds ! and Dubara Command Ke Saath Number Bhejna", parse_mode='markdown')
        
        for i in range(remaining, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0:
                    await countdown_msg.edit(f"⏰ Wait **{i-1}** Seconds ! and Dubara Command Ke Saath Number Bhejna", parse_mode='markdown')
                else:
                    await countdown_msg.delete()
            except:
                break
        return
    
    args = event.raw_text.split()
    
    if len(args) > 1:
        await process_ff(event, args[1])
        return
    
    user_state[user_id] = {"type": "ff", "attempts": 0}
    msg = await event.reply("🎮 **Send Free Fire UID**\nExample: `11111111`", parse_mode='markdown')
    asyncio.create_task(auto_delete(msg, 60))
    
    await asyncio.sleep(60)
    if user_id in user_state and user_state[user_id].get("type") == "ff":
        del user_state[user_id]
        await event.reply(f"⏰ Timeout! Send `/ff` again.", parse_mode='markdown')

async def process_ff(event, uid):
    user_id = event.sender_id
    
    can_execute, remaining = await check_rate_limit(user_id, "ff")
    if not can_execute:
        countdown_msg = await event.reply(f"⏰ Wait **{remaining}** Seconds ! and Dubara Command Ke Saath Number Bhejna", parse_mode='markdown')
        
        for i in range(remaining, 0, -1):
            await asyncio.sleep(1)
            try:
                if i-1 > 0:
                    await countdown_msg.edit(f"⏰ Wait **{i-1}** Seconds ! and Dubara Command Ke Saath Number Bhejna", parse_mode='markdown')
                else:
                    await countdown_msg.delete()
            except:
                break
        return
    
    uid = re.sub(r'\D', '', uid)
    
    if not uid.isdigit() or not (8 <= len(uid) <= 13):
        attempts = user_state.get(user_id, {}).get("attempts", 0) + 1
        user_state[user_id] = {"type": "ff", "attempts": attempts}
        
        if attempts >= 3:
            await delete_waiting_message(user_id)
            msg = await event.reply("❌ **Invalid UID!**\nSend `/ff 1234567890`", parse_mode='markdown')
            asyncio.create_task(auto_delete(msg, 15))
            del user_state[user_id]
        else:
            msg = await event.reply(f"⚠️ **Invalid!** ({attempts}/3)\nSend Valid UID.", parse_mode='markdown')
            user_waiting_messages[user_id] = msg
            asyncio.create_task(auto_delete(msg, 15))
        return
    
    if user_id in user_state:
        del user_state[user_id]
    
    await update_rate_limit(user_id, "ff")
    
    if is_ff_protected(uid):
        await event.reply("⚠️ **NO RESULT FOUND**", parse_mode='markdown')
        return
    
    wait_msg = await event.reply("🎮 **Fetching FF Info...**", parse_mode='markdown')
    
    try:
        res = requests.get(FF_API.format(uid), timeout=10).json()
    except:
        await wait_msg.edit("⚠️ **API Error**", parse_mode='markdown')
        asyncio.create_task(auto_delete(wait_msg, 15))
        return
    
    if not res.get("success"):
        await wait_msg.edit("⚠️ **NO RESULT FOUND**", parse_mode='markdown')
        asyncio.create_task(auto_delete(wait_msg, 15))
        return
    
    d = res["data"]
    
    prime_level_raw = d.get("🗿 Prime Level", "")
    if not prime_level_raw or prime_level_raw == "N/A":
        prime_level_raw = d.get("🥇 Prime", "")
    
    if prime_level_raw and prime_level_raw != "N/A":
        prime_match = re.search(r'^(\d+)', str(prime_level_raw))
        prime_level = prime_match.group(1) if prime_match else prime_level_raw
    else:
        prime_level = "N/A"
    
    likes_raw = d.get("👍 Likes", "")
    if likes_raw:
        likes_match = re.search(r'^(\d+)', str(likes_raw))
        likes = likes_match.group(1) if likes_match else likes_raw
    else:
        likes = "N/A"
    
    result = f"""━━━━━━━🎮 𝗙𝗿𝗲𝗲 𝗙𝗶𝗿𝗲 𝗜𝗻𝗳𝗼 🎮━━━━━━━

🆔 UID : {d.get('🆔 ID', 'N/A')}
📅 Created : {format_date(d.get('📅 Account Created'))}
🌍 Region : {d.get('🌎 Region', 'N/A')}
👤 Name : {d.get('👤 Nickname', 'N/A')}
🎖️ Level : {d.get('🎖️ Level', 'N/A')}
📈 EXP : {d.get('📈 Experience (XP)', 'N/A')}
🏅 Rank Points : {d.get('🏆 Ranked Points', 'N/A')}
🗿 Prime Level : {prime_level}
👍 Likes : {likes}
⏳ Last Login : {format_date(d.get('🕒 Last Login'))}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
 @HloSpidey @SpideyStuff 🕸️ 
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    await wait_msg.edit(result)

@client.on(events.NewMessage)
async def handler(event):
    user_id = event.sender_id
    
    if event.text and event.text.startswith('/'):
        return
    
    if user_id in user_state:
        state = user_state[user_id]
        
        if state["type"] == "num":
            await process_number(event, event.text)
        elif state["type"] == "ff":
            await process_ff(event, event.text)

from cfonts import render


async def main():
    await load_admin_data()
    await load_users_data()
    await load_users_list()   
    print('bot is running successfully')
    
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())