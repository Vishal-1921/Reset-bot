import os
os.environ['TERM'] = 'xterm'
import requests
import time
import re
import asyncio
import json
import traceback
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError, ChannelPrivateError, UserNotParticipantError

BOT_TOKEN = "8655956389:AAFSY3J8j6kfv6e_J-uFa3rviav2dKKLxXc"
API_ID = 6
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
ADMIN_IDS = [1725301348]
CONTACT_LINK = "https://t.me/HloSpidey"
CHANNEL_LINK = "https://t.me/+J-0a5CaeIZZiYzNl"
PHOTO_URL = "https://raw.githubusercontent.com/HloSpidey/photo/refs/heads/main/ss.jpg"
STORAGE_CHANNEL = -1003666940027
USERS_LIST_MSG_ID = 30
NUM_API = "https://hlospidey-7.vercel.app/api/number?num={}"
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
    "family": False
}

user_state = {}
user_last_command = defaultdict(float)
user_last_family_command = defaultdict(float)
request_count = 0
family_request_count = 0
request_window_start = time.time()
family_request_window_start = time.time()
cooldown_active = False
family_cooldown_active = False
cooldown_users = set()
family_cooldown_users = set()
users_list = set()
user_access = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def add_user(user_id):
    if user_id not in users_list and not is_admin(user_id):
        users_list.add(user_id)
        if user_id not in user_access:
            user_access[user_id] = {"num": 0, "family": 0}
        asyncio.create_task(update_users_list_msg())

def get_user_access_days(user_id, feature):
    if is_admin(user_id):
        return 999999
    access = user_access.get(user_id, {"num": 0, "family": 0})
    days = access.get(feature, 0)
    if days > 0:
        expiry = user_access.get(user_id, {}).get(f"{feature}_expiry", 0)
        if expiry < time.time():
            user_access[user_id][feature] = 0
            asyncio.create_task(update_users_list_msg())
            return 0
    return days

def set_user_access(user_id, feature, days):
    if user_id not in user_access:
        user_access[user_id] = {"num": 0, "family": 0}
    user_access[user_id][feature] = days
    user_access[user_id][f"{feature}_expiry"] = time.time() + (days * 86400)
    asyncio.create_task(update_users_list_msg())

def remove_user_access(user_id, feature):
    if user_id in user_access:
        user_access[user_id][feature] = 0
        user_access[user_id][f"{feature}_expiry"] = 0
        asyncio.create_task(update_users_list_msg())

def get_all_users():
    return list(users_list)

def get_user_count():
    return len(users_list)

async def update_users_list_msg():
    try:
        msg_text = "📊 **Users List** 📊\n\n"
        for uid in sorted(users_list):
            num_days = user_access.get(uid, {}).get("num", 0)
            fam_days = user_access.get(uid, {}).get("family", 0)
            msg_text += f"👤 `{uid}` 🟢{num_days} 🔵{fam_days}\n"
        await client.edit_message(STORAGE_CHANNEL, USERS_LIST_MSG_ID, msg_text, parse_mode='markdown')
    except Exception as e:
        print(f"Error updating users list: {e}")

async def load_users_list():
    global users_list, user_access
    try:
        msg = await client.get_messages(STORAGE_CHANNEL, ids=USERS_LIST_MSG_ID)
        if msg and msg.text:
            users_list = set()
            user_access = {}
            for line in msg.text.split('\n'):
                if '`' in line:
                    parts = line.split('`')
                    uid_str = parts[1]
                    if uid_str.isdigit():
                        uid = int(uid_str)
                        users_list.add(uid)
                        rest = line.split('`')[-1].strip()
                        num_days = 0
                        fam_days = 0
                        if '🟢' in rest:
                            num_part = rest.split('🟢')[1].split()[0]
                            if num_part.isdigit():
                                num_days = int(num_part)
                        if '🔵' in rest:
                            fam_part = rest.split('🔵')[1].split()[0]
                            if fam_part.isdigit():
                                fam_days = int(fam_part)
                        user_access[uid] = {"num": num_days, "family": fam_days}
    except Exception as e:
        print(f"Error loading users list: {e}")
        users_list = set()
        user_access = {}

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
    global request_count, family_request_count
    if api_type == 'num':
        request_count += 1
    else:
        family_request_count += 1

async def send_verification_message(event):
    photo_url = PHOTO_URL
    caption = "**I'm Num+Family Info Bot 📡 With Unlimited Searches 🚀** \n\n⚠️ **Join All Channels To Use The Bot**"
    buttons = [
        [Button.url("[ 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝟭 ]", VERIFY_LINK_1), Button.url("[ 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝟮 ]", VERIFY_LINK_2)],
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
    caption = "**I'm Num+Family Info Bot 📡 With Unlimited Searches 🚀**\n\n⚙️ **My Commands:**\n\n/num - **Get Number Info 📱**\n/family - **Get Family Members Name 👨‍👩‍👧‍👦**"
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
        await message.reply("🔧 **Number Info API is Under Maintenance**\n\n📡 **You can still use:**\n• /family - **Family Members Name**\n\n⚡ **Api On Hote Hee Bot Msg Bhej Dega.**", parse_mode='markdown')
        return
    try:
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
                filename = f"{num}_{now}.txt"
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

async def process_family(event, aadhar):
    client = event.client
    message = event
    user_id = message.sender_id
    if api_locks["family"] and not is_admin(user_id):
        await message.reply("🔧 **Family Data API is Under Maintenance**\n\n📡 **You can still use :**\n• /num - **Number Information**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
        return
    try:
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
                        caption=f"📄 Family data for Aadhar `{aadhar}`"
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

client = TelegramClient('SpideyLimitedOSINTBot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_waiting_messages = {}

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
        await event.reply("🔧 **Number Info API is Under Maintenance**\n\n📡 **You can still use:**\n• /family - **Family Members Name**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
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
    days_left = get_user_access_days(user_id, 'num')
    if days_left <= 0 and not is_admin(user_id):
        await event.reply(f"Hey {event.sender.first_name} , You Don't Have Premium Access To Use This Bot. Access Plan :\n\nMonthly Unlimited Searches : ~~300~~ ❌ **200**rs. Only ! ✅\nWeekly Unlimited Searches : 100rs\n\nContact @HloSpidey For Unlimited Access.", parse_mode='markdown')
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

@client.on(events.NewMessage(pattern=r'^/family'))
async def family_command(event):
    user_id = event.sender_id
    add_user(user_id)
    if all(api_locks.values()) and not is_admin(user_id):
        await event.reply("🔒 **All APIs are Locked By Spidey** 🕸️\n\n📡 **APIs Activate Hote Hee Bot Tujhe Msg Bhej Dega** ⚡", parse_mode='markdown')
        return
    if api_locks["family"] and not is_admin(user_id):
        await event.reply("🔧 **Family Data API is Under Maintenance**\n\n📡 **You can still use :**\n• /num - **Number Information**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
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
    days_left = get_user_access_days(user_id, 'family')
    if days_left <= 0 and not is_admin(user_id):
        await event.reply(f"Bro {event.sender.first_name} , You Don't Have Access To This Feature 🥀 Get Monthly Access For Family Info in 50rs.", parse_mode='markdown')
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
        await event.reply("`/lock num` — `/lock family` — `/lock all` \n\n`/unlock num` — `/unlock family` — `/unlock all`", parse_mode='markdown')
        return
    command = parts[0].replace('/', '')
    target = parts[1].lower()
    if command == "lock":
        if target == "all":
            api_locks["num"] = True
            api_locks["family"] = True
            await event.reply("🔒 **All APIs Are Locked by Spidey!**\n\n🔒 **Locked Successfully 🔒✅**\n\n⚡ `/unlock all`", parse_mode='markdown')
        elif target in api_locks:
            api_locks[target] = True
            api_names = {"num": "Number Info", "family": "Family Data"}
            await event.reply(f"🔒 **{api_names[target]} API Has Been Locked Successfully!**\n\n⚡ Use `/unlock {target}`", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Option!** Use: num, family, or all", parse_mode='markdown')
    elif command == "unlock":
        if target == "all":
            api_locks["num"] = False
            api_locks["family"] = False
            await event.reply("🔓 **All APIs Have Been Unlocked Successfully!**\n\n✅ All search services are now available for everyone.\n\n📡 Enjoy unlimited free searches! 🚀", parse_mode='markdown')
        elif target in api_locks:
            api_locks[target] = False
            api_names = {"num": "Number Info", "family": "Family Data"}
            await event.reply(f"🔓 **{api_names[target]} API Has Been Unlocked Successfully!**\n\n✅ The service is now available for all users.\n\n📡 Search without any restrictions! 🚀", parse_mode='markdown')
        else:
            await event.reply("❌ **Invalid Option!** Use: num, family, or all", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/addnum\s', func=lambda e: is_admin(e.sender_id)))
async def addnum_command(event):
    parts = event.text.split()
    if len(parts) < 3:
        await event.reply("❌ **Usage:** `/addnum user_id days`", parse_mode='markdown')
        return
    try:
        user_id = int(parts[1])
        days = int(parts[2])
        set_user_access(user_id, "num", days)
        await event.reply(f"✅ `{user_id}` has been granted access for {days} days (Number Info) ✅", parse_mode='markdown')
        try:
            user = await client.get_entity(user_id)
            first_name = user.first_name
            await client.send_message(user_id, f"Hey {first_name} ! You Have Access To Number Info Feature For {days} Days 🎉", parse_mode='markdown')
        except:
            pass
    except ValueError:
        await event.reply("❌ **Invalid User ID or Days!**", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/addfam\s', func=lambda e: is_admin(e.sender_id)))
async def addfam_command(event):
    parts = event.text.split()
    if len(parts) < 3:
        await event.reply("❌ **Usage:** `/addfam user_id days`", parse_mode='markdown')
        return
    try:
        user_id = int(parts[1])
        days = int(parts[2])
        set_user_access(user_id, "family", days)
        await event.reply(f"✅ `{user_id}` has been granted access for {days} days (Family Info) ✅", parse_mode='markdown')
        try:
            user = await client.get_entity(user_id)
            first_name = user.first_name
            await client.send_message(user_id, f"Hey {first_name} ! You Have Access To Family Info Feature For {days} Days 🎉", parse_mode='markdown')
        except:
            pass
    except ValueError:
        await event.reply("❌ **Invalid User ID or Days!**", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/add\s', func=lambda e: is_admin(e.sender_id)))
async def add_command(event):
    parts = event.text.split()
    if len(parts) < 3:
        await event.reply("❌ **Usage:** `/add user_id days`", parse_mode='markdown')
        return
    try:
        user_id = int(parts[1])
        days = int(parts[2])
        set_user_access(user_id, "num", days)
        set_user_access(user_id, "family", days)
        await event.reply(f"✅ `{user_id}` has been granted access for {days} days (Both Features) ✅", parse_mode='markdown')
        try:
            user = await client.get_entity(user_id)
            first_name = user.first_name
            await client.send_message(user_id, f"Hey {first_name} ! You Have Access To Both Features For {days} Days 🎉", parse_mode='markdown')
        except:
            pass
    except ValueError:
        await event.reply("❌ **Invalid User ID or Days!**", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/stopnum\s', func=lambda e: is_admin(e.sender_id)))
async def stopnum_command(event):
    parts = event.text.split()
    if len(parts) < 2:
        await event.reply("❌ **Usage:** `/stopnum user_id`", parse_mode='markdown')
        return
    try:
        user_id = int(parts[1])
        remove_user_access(user_id, "num")
        await event.reply(f"✅ `{user_id}` Number Info access stopped ✅", parse_mode='markdown')
        try:
            user = await client.get_entity(user_id)
            first_name = user.first_name
            await client.send_message(user_id, f"Hey {first_name} ! Your Number Info Access Has Been Revoked. ⌛🥀 Contact @HloSpidey To Get Monthly Unlimited Access in **200rs** .", parse_mode='markdown')
        except:
            pass
    except ValueError:
        await event.reply("❌ **Invalid User ID!**", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/stopfam\s', func=lambda e: is_admin(e.sender_id)))
async def stopfam_command(event):
    parts = event.text.split()
    if len(parts) < 2:
        await event.reply("❌ **Usage:** `/stopfam user_id`", parse_mode='markdown')
        return
    try:
        user_id = int(parts[1])
        remove_user_access(user_id, "family")
        await event.reply(f"✅ `{user_id}` Family Info access stopped ✅", parse_mode='markdown')
        try:
            user = await client.get_entity(user_id)
            first_name = user.first_name
            await client.send_message(user_id, f"Hey {first_name} ! Your Family Info Access Has Been Revoked. ⌛🥀 Contact @HloSpidey To Get Monthly Unlimited Access in **100rs** .", parse_mode='markdown')
        except:
            pass
    except ValueError:
        await event.reply("❌ **Invalid User ID!**", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/stop\s', func=lambda e: is_admin(e.sender_id)))
async def stop_command(event):
    parts = event.text.split()
    if len(parts) < 2:
        await event.reply("❌ **Usage:** `/stop user_id`", parse_mode='markdown')
        return
    try:
        user_id = int(parts[1])
        remove_user_access(user_id, "num")
        remove_user_access(user_id, "family")
        await event.reply(f"✅ `{user_id}` All access stopped ✅", parse_mode='markdown')
        try:
            user = await client.get_entity(user_id)
            first_name = user.first_name
            await client.send_message(user_id, f"Hey {first_name} ! Your Access Has Been Revoked. ⌛🥀 Contact @HloSpidey To Get Monthly Unlimited Access in **200rs** .", parse_mode='markdown')
        except:
            pass
    except ValueError:
        await event.reply("❌ **Invalid User ID  !**", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/send\s', func=lambda e: is_admin(e.sender_id)))
async def send_command(event):
    parts = event.text.split(maxsplit=2)
    if len(parts) < 3:
        await event.reply("❌ **Usage:** `/send user_id message`", parse_mode='markdown')
        return
    try:
        user_id = int(parts[1])
        msg_text = parts[2]
        await client.send_message(user_id, msg_text, parse_mode='markdown')
        await event.reply(f"✅ Message sent to `{user_id}`", parse_mode='markdown')
    except ValueError:
        await event.reply("❌ **Invalid User ID !**", parse_mode='markdown')
    except Exception as e:
        await event.reply(f"❌ Failed to send: {str(e)}", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/help$', func=lambda e: is_admin(e.sender_id)))
async def help_command(event):
    help_text = """
📖 **Admin Commands Help** 📖

🔧 **API Control:**
`/lock num` - Lock Number API
`/lock family` - Lock Family API
`/lock all` - Lock All APIs
`/unlock num` - Unlock Number API
`/unlock family` - Unlock Family API
`/unlock all` - Unlock All APIs

👥 **Access Management:**
`/addnum <user_id> <days>` - Grant Number access
`/addfam <user_id> <days>` - Grant Family access
`/add <user_id> <days>` - Grant Both access
`/stopnum <user_id>` - Revoke Number access
`/stopfam <user_id>` - Revoke Family access
`/stop <user_id>` - Revoke Both access

📊 **Statistics:**
`/stats` - Show premium users & days left

📢 **Other:**
`/send <user_id> <msg>` - Send message to user
`/v1 <channel_id> <link>` - Update verify channel 1
`/v2 <channel_id> <link>` - Update verify channel 2
`/gc <link>` - Update group link
`/ch <link>` - Update channel link

👑 **Admin Management:**
`/addadmin <user_id>` - Add new admin
`/removeadmin <user_id>` - Remove admin
`/listadmins` - List all admins
"""
    await event.reply(help_text, parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/stats$', func=lambda e: is_admin(e.sender_id)))
async def stats_command(event):
    premium_users = []
    for uid in users_list:
        num_days = get_user_access_days(uid, 'num')
        fam_days = get_user_access_days(uid, 'family')
        if num_days > 0 or fam_days > 0:
            try:
                user = await client.get_entity(uid)
                name = user.first_name
            except:
                name = str(uid)
            premium_users.append((uid, name, num_days, fam_days))
    if not premium_users:
        await event.reply("📊 **No premium users found.**", parse_mode='markdown')
        return
    text = "👑 **Premium Users List** 👑\n\n"
    for uid, name, num_d, fam_d in premium_users:
        text += f"👤 **{name}**\n"
        text += f"🆔 `{uid}`\n"
        text += f"📞 Number: {num_d} days left\n"
        text += f"👨‍👩‍👧 Family: {fam_d} days left\n\n"
    await event.reply(text, parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/v1\s', func=lambda e: is_admin(e.sender_id)))
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

@client.on(events.NewMessage(pattern=r'^/v2\s', func=lambda e: is_admin(e.sender_id)))
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

@client.on(events.NewMessage(pattern=r'^/gc\s', func=lambda e: is_admin(e.sender_id)))
async def update_gc_link(event):
    global current_gc_link
    parts = event.text.split(maxsplit=1)
    if len(parts) > 1:
        current_gc_link = parts[1]
        await event.reply("✅ **Group Link Updated Successfully**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/gc https://t.me/group_link`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/ch\s', func=lambda e: is_admin(e.sender_id)))
async def update_ch_link(event):
    global current_ch_link
    parts = event.text.split(maxsplit=1)
    if len(parts) > 1:
        current_ch_link = parts[1]
        await event.reply("✅ **Channel Link Updated Successfully**", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/ch https://t.me/channel_link`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/addadmin\s', func=lambda e: is_admin(e.sender_id)))
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
            await event.reply("❌ **Invalid User ID !** Use: `/addadmin 123456789`", parse_mode='markdown')
    else:
        await event.reply("❌ **Usage:** `/addadmin user_id`", parse_mode='markdown')

@client.on(events.NewMessage(pattern=r'^/removeadmin\s', func=lambda e: is_admin(e.sender_id)))
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

@client.on(events.NewMessage(pattern=r'^/listadmins$', func=lambda e: is_admin(e.sender_id)))
async def list_admins_command(event):
    admin_list = "\n".join([f"👑 `{aid}`" for aid in ADMIN_IDS])
    await event.reply(f"**👥 Admin List:**\n\n{admin_list}", parse_mode='markdown')

@client.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    data = event.data.decode()
    if data == "verify_member":
        is_member = await check_membership(user_id)
        if is_member:
            await event.delete()
            add_user(user_id)
            photo_url = PHOTO_URL
            caption = "**I'm Num+Family Info Bot 📡 With Unlimited Searches 🚀**\n\n⚙️ **My Commands :**\n\n/num - **Get Number Info 📱**\n/family - **Get Family Members Name 👨‍👩‍👧‍👦**"
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
    if user_id not in user_state:
        return
    state = user_state[user_id]
    state_type = state.get("type")
    if state_type == "waiting_num":
        add_user(user_id)
        if all(api_locks.values()) and not is_admin(user_id):
            await event.reply("🔒 **All APIs are Locked By Spidey** 🕸️\n\n📡 **APIs Activate Hote Hee Bot Tujhe Msg Bhej Dega** ⚡", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        if api_locks["num"] and not is_admin(user_id):
            await event.reply("🔧 **Number Info API is Under Maintenance**\n\n📡 **You can still use:**\n• /family - **Family Members Name**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        days_left = get_user_access_days(user_id, 'num')
        if days_left <= 0 and not is_admin(user_id):
            await event.reply(f"Hey {event.sender.first_name} , You Don't Have Premium Access To Use This Bot. Access Plan :\n\nMonthly Unlimited Searches : ~~300~~ ❌ **200**rs. Only ! ✅\nWeekly Unlimited Searches : 100rs\n\nContact @HloSpidey For Unlimited Access.", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        num = extract_number(event.text)
        if not num:
            await event.reply("❌ **Invalid number ! Send a 10-digit phone number.**", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        update_rate_limit(user_id, 'num')
        await process_number(event, num)
        del user_state[user_id]
        await delete_user_messages(user_id)
    elif state_type == "waiting_family":
        add_user(user_id)
        if all(api_locks.values()) and not is_admin(user_id):
            await event.reply("🔒 **All APIs are Locked By Spidey** 🕸️\n\n📡 **APIs Activate Hote Hee Bot Tujhe Msg Bhej Dega** ⚡", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        if api_locks["family"] and not is_admin(user_id):
            await event.reply("🔧 **Family Data API is Under Maintenance**\n\n📡 **You can still use :**\n• /num - **Number Information**\n\n⚡ Api On Hote Hee Bot Msg Bhej Dega.", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        is_member = await check_membership(user_id)
        if not is_member:
            await send_verification_message(event)
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        days_left = get_user_access_days(user_id, 'family')
        if days_left <= 0 and not is_admin(user_id):
            await event.reply(f"Bro {event.sender.first_name} , You Don't Have Access To This Feature, Get Monthly Access For Family Info in 50rs. Only. Contact @HloSpidey For Unlimited Access" , parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        aadhar = extract_aadhar(event.text)
        if not aadhar:
            await event.reply("❌ **Invalid Aadhar ! Send a 12-digit Aadhar number.**", parse_mode='markdown')
            del user_state[user_id]
            await delete_user_messages(user_id)
            return
        update_rate_limit(user_id, 'family')
        await process_family(event, aadhar)
        del user_state[user_id]
        await delete_user_messages(user_id)

@client.on(events.NewMessage)
async def group_restriction(event):
    if event.is_group and not is_admin(event.sender_id):
        await event.reply("⚠️ **Use Me In Private Chat Only**", buttons=[[Button.url("📩 Start Bot", f"https://t.me/{client.me.username}")]], parse_mode='markdown')
        return

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
