import requests as rq,time,random,json,os,re,asyncio,hashlib,uuid
from telethon import TelegramClient,events,Button
from concurrent.futures import ThreadPoolExecutor
from user_agent import generate_user_agent
from datetime import datetime
from cfonts import render

BOT_TOKEN="8465467291:AAHvxM0tn-4pMZr8_5pJMrBMBsVRdr235yg"
API_ID=6
API_HASH="eb06d4abfb49dc3eeb1aeb98ae0f581e"
ADMIN_ID=1725301348
CHANNEL_USERNAME="@SpideyStuff"
CHANNEL_ID=-1002744702466
SESSION_IDS=[
    "78156611401%3AAKVdgbPAEcozj0%3A22%3AAYgHQrQ7g9AvMUXCFnVXlAOgjqw2Nv2myGJhJC4lzQ",
    "78157675209%3AwJpsJTC10bFFA0%3A27%3AAYh82tRHwp6KJTddwz7Duldn40uBcHWezrEhO4xMJw",
    "78266621813%3Av91kPuKtkbqdwS%3A0%3AAYhWKKVO9_IYsVB6pb8Pu9fP6Zh9EwH3UtLNnq6quA",
    "77958465669%3ASiWF2jJ5lnUjQW%3A0%3AAYj6-iKk4qDF-wVQKlxDDLSMPUSv-G_JeQcQ05HuGA",
    "78287133697%3AzrnS0vUZcy0wp6%3A5%3AAYiuOdxHSn1EsmVrktQc29zwtCv6DPvH5LEEECIneg",
    "78528400527%3AhJZ3bSsHRuIJ69%3A0%3AAYjzHSItumBi_CWg3GpoPh_jads9gCIYvysL1wDeiw"
]
PROXIES_LIST=[]
client=TelegramClient('reset_bot7_session',API_ID,API_HASH).start(bot_token=BOT_TOKEN)
users_file="users.txt"
verified_file="verified.txt"
trial_file="trial.txt"
broadcast_active=False
bot_start=time.time()
user_states={}
processed_msgs=set()
user_cooldown={}
sent_broadcasts={}
channel_link="https://t.me/SpideyStuff"
def log_act(msg):
    t=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log=f"[{t}] {msg}"
    print(log)
    with open("log.txt","a",encoding="utf-8")as f:f.write(log+"\n")
    
class InstaReset:
    def __init__(self):self.sessions=self.create_sessions();self.cur_method="api"
    def create_sessions(self):
        s=[];i=1
        for sid in SESSION_IDS:
            if sid and sid!="YOUR_SESSION_ID_1":
                se=rq.Session();se.cookies.update({'sessionid':sid});se.num=i;s.append(se);i+=1
        return s
    def get_proxy(self):return random.choice(PROXIES_LIST)if PROXIES_LIST else None
    def get_session(self):return random.choice(self.sessions)if self.sessions else None
    def test_api(self):
        try:se=rq.Session();r=se.get("https://www.instagram.com/accounts/password/reset/?source=fxcal",headers={"User-Agent":generate_user_agent()},timeout=10);return r.status_code==200
        except:return False
    def test_session(self,se,num):
        try:
            h={'User-Agent':'Instagram 100.0.0.17.129 Android','Content-Type':'application/x-www-form-urlencoded'}
            d={'email_or_username':'nonexistent_test_account_12345','flow':'fxcal'};r=se.post('https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/',headers=h,data=d,timeout=10);return r.status_code in[200,400]
        except Exception as e:print(f"Session {num} error: {e}");return False
    def extract_user(self,t):
        if"instagram.com/"in t:m=re.search(r"instagram\.com/([a-zA-Z0-9._]+)",t);return m.group(1)if m else None
        return t.strip().lstrip('@')
    def api_reset(self,acc,proxy=None):
        try:
            se=rq.Session();p={'http':proxy,'https':proxy}if proxy else None;r=se.get("https://www.instagram.com/accounts/password/reset/?source=fxcal",headers={"User-Agent":generate_user_agent()},proxies=p,timeout=10)
            m=re.search(r'"csrf_token":"([^"]+)"',r.text);c=m.group(1)if m else hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:32]
            h={"authority":"www.instagram.com","accept":"*/*","content-type":"application/x-www-form-urlencoded","cookie":f"csrftoken={c};","origin":"https://www.instagram.com","referer":"https://www.instagram.com/accounts/password/reset/?source=fxcal","user-agent":generate_user_agent(),"x-csrftoken":c,"x-ig-app-id":"1217981644879628","x-requested-with":"XMLHttpRequest"}
            u=self.extract_user(acc);d={"email_or_username":u,"flow":"fxcal"};r=se.post("https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",headers=h,data=d,proxies=p,timeout=10);return self.parse_resp(r,u,acc,"API")
        except Exception as e:return{'success':False,'message':f'API Error: {str(e)}','input':acc,'method':'API'}
    def session_reset(self,acc,proxy=None):
        try:
            se=self.get_session();p={'http':proxy,'https':proxy}if proxy else None
            if not se:return{'success':False,'message':'No valid sessions','input':acc,'method':'Session'}
            h={'User-Agent':'Instagram 100.0.0.17.129 Android','Content-Type':'application/x-www-form-urlencoded'};d={'email_or_username':self.extract_user(acc),'flow':'fxcal'};r=se.post('https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/',headers=h,data=d,proxies=p,timeout=10);n=getattr(se,'num','Unknown');return self.parse_resp(r,self.extract_user(acc),acc,f"Session {n}")
        except Exception as e:return{'success':False,'message':f'Session Error: {str(e)}','input':acc,'method':'Session'}
    def send_req(self,acc):
        u=self.extract_user(acc);p=self.get_proxy();m=['api','session'];random.shuffle(m);pm=m[0];fb=m[1]if len(m)>1 else None
        if pm=='api':res=self.api_reset(acc,p)
        else:res=self.session_reset(acc,p)
        if not res['success']and fb:log_act(f"Switch {pm} to {fb} for {u}");res=self.api_reset(acc,p)if fb=='api'else self.session_reset(acc,p)
        return res
    def parse_resp(self,r,pi,oi,m):
        try:
            d=r.json()
            if d.get('status')=='ok':mc=self.extract_masked(d,pi);return{'success':True,'message':'Password Reset Sent Successfully!','display_input':mc,'input':oi,'masked_contact':mc,'method':m}
            else:return{'success':False,'message':d.get('message','Unknown Error'),'input':oi,'masked_contact':None,'method':m}
        except Exception as e:return{'success':False,'message':f'Parse Error: {str(e)}','input':oi,'masked_contact':None,'method':m}
    def extract_masked(self,d,pi):
        try:
            m=d.get('message','');e=re.search(r'[a-zA-Z0-9*]+\*+[a-zA-Z0-9*]*@[a-zA-Z0-9*.-]+\.[a-zA-Z]{2,}',m)
            if e:return e.group(0)
            p=re.search(r'\*{3}\s*\*{3}\s*\d{4}',m)
            if p:return p.group(0)
            if'@'in pi:return self.mask_email(pi)
            else:return f"@{pi}"
        except:
            if'@'in pi:return self.mask_email(pi)
            else:return f"@{pi}"
    def mask_email(self,e):
        if'@'not in e:return e
        u,d=e.split('@');m=u[0]+'*'*(len(u)-2)+u[-1]if len(u)>2 else u[0]+'*';return f"{m}@{d}"

bot=InstaReset()
def save_user(uid):
    try:
        with open(users_file,'a+',encoding='utf-8')as f:f.seek(0);e=set(line.strip()for line in f if line.strip())
        if str(uid)not in e:f.write(f"{uid}\n")
    except:pass
def save_verified(uid):
    try:
        with open(verified_file,'a+',encoding='utf-8')as f:f.seek(0);e=set(line.strip()for line in f if line.strip())
        if str(uid)not in e:f.write(f"{uid}\n")
    except:pass
def mark_trial(uid):
    try:
        with open(trial_file,'a+',encoding='utf-8')as f:f.seek(0);e=set(line.strip()for line in f if line.strip())
        if str(uid)not in e:f.write(f"{uid}\n")
    except:pass
def used_trial(uid):
    try:
        with open(trial_file,'r',encoding='utf-8')as f:u=set(line.strip()for line in f if line.strip());return str(uid)in u
    except:return False
def is_verified(uid):
    try:
        with open(verified_file,'r',encoding='utf-8')as f:u=set(line.strip()for line in f if line.strip());return str(uid)in u
    except:return False
async def check_member(uid):
    if uid==ADMIN_ID:return True
    try:await client.get_permissions(CHANNEL_ID,uid);return True
    except:pass
    try:p=await client.get_participants(CHANNEL_ID);u=[user.id for user in p];return uid in u
    except:pass
    try:from telethon.tl.functions.channels import GetParticipantRequest;await client(GetParticipantRequest(CHANNEL_ID,uid));return True
    except:return False
    
def old_msg(e):
    try:m=e.message.date.timestamp();return m<bot_start
    except:return False

async def require_member(e):
    uid=e.sender_id;save_user(uid)
    if uid in user_states:return True
    if e.text and e.text.startswith('/'):
        if not used_trial(uid):mark_trial(uid);return True
        if await check_member(uid):save_verified(uid);return True
        else:
            m=[[Button.url("𝗖𝗵𝗮𝗻𝗻𝗲𝗹 🚀",channel_link)],[Button.inline("𝗜'𝘃𝗲 𝗝𝗼𝗶𝗻𝗲𝗱 ✅","verify_member")]]
            try:await e.reply("**Join Channel To Use The Bot 🔒🤖**",file='https://raw.githubusercontent.com/HloSpidey/Insta-Acc-Creater/refs/heads/main/ss.jpg',buttons=m)
            except:await e.reply("**Join Channel To Use The Bot 🔒🤖**",buttons=m)
            return False
    else:return True

@client.on(events.NewMessage)
async def msg_handler(e):
    if old_msg(e):return
    mid=e.message.id
    if mid in processed_msgs:return
    processed_msgs.add(mid)
    if len(processed_msgs)>1000:processed_msgs.clear()
    t=e.text or""
    if t.startswith('/start'):await start_h(e)
    elif t.startswith('/reset'):await reset_h(e)
    elif t.startswith('/bulk'):await bulk_h(e)
    elif t.startswith('/stats'):await stats_h(e)
    elif t.startswith('/broadcast'):await broadcast_h(e)
    elif t.startswith('/check'):await check_h(e)
    elif t.startswith('/addlink')and e.sender_id==ADMIN_ID:await addlink_h(e)
    elif t.startswith('/addsession')and e.sender_id==ADMIN_ID:await addsession_h(e)
    elif t.startswith('/manage_sessions')and e.sender_id==ADMIN_ID:await manage_sessions_h(e)
    elif e.sender_id in user_states:
        s=user_states[e.sender_id].get('state')
        if s=='waiting_reset':await process_reset_h(e)
        elif s=='waiting_bulk':await process_bulk_h(e)
        elif s=='waiting_link':await process_link_h(e)
        elif s=='waiting_session':await process_session_h(e)

async def start_h(e):
    uid=e.sender_id;save_user(uid)
    if uid in user_states:del user_states[uid]
    m=[[Button.url("🕷️𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗠𝗲","https://t.me/HloSpidey"),Button.url("𝗖𝗵𝗮𝗻𝗻𝗲𝗹🕷️",channel_link)]]
    cap="**I'M Reset Bot , By @HloSpidey**\n\n**Use My Commands:**\n/reset - Single Email / Username\n/bulk - Bulk Accounts Reset"
    try:await e.reply(cap,file='https://raw.githubusercontent.com/HloSpidey/Insta-Acc-Creater/refs/heads/main/ss.jpg',buttons=m)
    except:await e.reply(cap,buttons=m)

async def reset_h(e):
    if not await require_member(e):return
    uid=e.sender_id;cid=e.chat_id;user_states[uid]={'state':'waiting_reset','chat_id':cid};await e.reply("**Send Any Email Or Username :**")

async def process_reset_h(e):
    uid=e.sender_id;cid=e.chat_id
    if uid not in user_states or user_states[uid].get('chat_id')!=cid:return
    ui=e.text.strip()
    if ui.startswith('/'):
        if uid in user_states:del user_states[uid]
        if ui.lower()=='/reset':await reset_h(e);return
        elif ui.lower()=='/bulk':await bulk_h(e);return
        elif ui.lower()=='/start':await start_h(e);return
        else:
            if uid in user_states:del user_states[uid];return
    if uid in user_states:del user_states[uid]
    pm=await e.reply("**Processing... 🔄**")
    with ThreadPoolExecutor() as ex:f=ex.submit(bot.send_req,ui);res=f.result()
    try:u=await client.get_entity(uid);un=f"@{u.username}"if u.username else f"UserID:{uid}"
    except:un=f"UserID:{uid}"
    se="✅"if res['success']else"❌";mu=res.get('method','Unknown');log_act(f"Single: {un} —> {ui} [{mu} {se}]")
    if res['success']:
        if'@'in ui:ud=bot.mask_email(ui)
        else:ud=f"@{bot.extract_user(ui)}"
        mc=res.get('masked_contact',res['display_input']);ft=f"**Pass Reset Sent Successfully {ui} :**\n\n[ {mc} ] ✅"
    else:ft=f"**Pass Reset Sent Failed :**\n\n{res['message']}"
    await pm.edit(ft)

async def bulk_h(e):
    if not await require_member(e):return
    uid=e.sender_id
    if uid in user_cooldown:
        tp=time.time()-user_cooldown[uid]
        if tp<10:rt=10-int(tp);await e.reply(f"**Wait {rt} Seconds For Next Bulk Reset.**\n**But You Can Use Single /Reset Command Now.**");return
    cid=e.chat_id;user_states[uid]={'state':'waiting_bulk','chat_id':cid}
    bi="""**Send MAX 10 Emails Or Usernames In This Style:**

zuck@gmail.com
ronaldo@aol.com
messi@hotmail.com
viratkohli
hwhe@hi2.in
kaksk@telegmail.com
@Spidey123

**You Can Send Any Mails Or Usernames Mix ✅**"""
    await e.reply(bi)

async def process_bulk_h(e):
    uid=e.sender_id;cid=e.chat_id
    if uid not in user_states or user_states[uid].get('chat_id')!=cid:return
    ui=e.text.strip()
    if ui.startswith('/'):
        if uid in user_states:del user_states[uid]
        if ui.lower()=='/reset':await reset_h(e);return
        elif ui.lower()=='/bulk':await bulk_h(e);return
        elif ui.lower()=='/start':await start_h(e);return
        else:
            if uid in user_states:del user_states[uid];return
    if uid in user_states:del user_states[uid]
    acc=[line.strip()for line in ui.split('\n')if line.strip()];acc=[a.lstrip('@')for a in acc]
    if len(acc)==1 and'\n'not in ui:
        pm=await e.reply("**Processing As Single Reset...🔄**")
        with ThreadPoolExecutor() as ex:f=ex.submit(bot.send_req,acc[0]);res=f.result()
        try:u=await client.get_entity(uid);un=f"@{u.username}"if u.username else f"UserID:{uid}"
        except:un=f"UserID:{uid}"
        se="✅"if res['success']else"❌";mu=res.get('method','Unknown');log_act(f"Single: {un} —> {acc[0]} [{mu} {se}]")
        if res['success']:
            if'@'in acc[0]:ud=bot.mask_email(acc[0])
            else:ud=f"@{bot.extract_user(acc[0])}"
            mc=res.get('masked_contact',res['display_input']);ft=f"**Pass Reset Sent Successfully {acc[0]} :**\n\n[ {mc} ] ✅"
        else:ft=f"**Pass Reset Sent Failed :**\n\n{res['message']}"
        await pm.edit(ft);return
    if len(acc)>10:await e.reply("**BULK RESET MAX LIMIT IS 10 - Using First 10 Items**");acc=acc[:10]
    pt="**Bulk Pass Reset In Progress:**\n\n"
    for i,a in enumerate(acc,1):pt+=f"{i}. {a}\n"
    pm=await e.reply(pt);res=[];se=["⏳"]*len(acc)
    for i,a in enumerate(acc):
        with ThreadPoolExecutor() as ex:f=ex.submit(bot.send_req,a);r=f.result();res.append(r);se[i]="✅"if r['success']else"❌"
        try:u=await client.get_entity(uid);un=f"@{u.username}"if u.username else f"UserID:{uid}"
        except:un=f"UserID:{uid}"
        s="✅"if r['success']else"❌";m=r.get('method','Unknown');log_act(f"Bulk: {un} —> {a} [{m} {s}]")
        ut="**Bulk Pass Reset In Progress:**\n\n"
        for j,ac in enumerate(acc):ut+=f"{j+1}. {ac} {se[j]}\n"
        await pm.edit(ut)
        if i<len(acc)-1:await asyncio.sleep(3)
    user_cooldown[uid]=time.time();sc=sum(1 for r in res if r['success']);fa=[r['input']for r in res if not r['success']]
    ft="**Bulk Reset Completed!**\n\n"
    for i,(a,r)in enumerate(zip(acc,res),1):em="✅"if r['success']else"❌";ft+=f"{i}. {a} {em}\n"
    ft+=f"\n**Success:** {sc}/{len(acc)}"
    if fa:fl="\n".join([f"• {ac}"for ac in fa]);ft+=f"\n\n**Failed:**\n{fl}\n\n**Try These With /Reset Command**"
    await pm.edit(ft)

async def check_h(e):
    uid=e.sender_id
    if uid!=ADMIN_ID:await e.reply("**You'Re Not Authorized To Use This Command**");return
    if e.is_group or e.is_channel:await e.reply("**This Command Works In Private Chat Only**");return
    sm=await e.reply("**Checking System Status...**\n\n**Checking In Progress:**\n1. ⏳\n"+"\n".join([f"{i+2}. ⏳"for i in range(len(bot.sessions))]))
    api_stat=bot.test_api();ae="✅"if api_stat else"❌";st=f"**Checking System Status...**\n\n**Checking In Progress:**\n1. {ae}\n";await sm.edit(st+"\n".join([f"{i+2}. ⏳"for i in range(len(bot.sessions))]))
    ss=[]
    for i,se in enumerate(bot.sessions):
        sess_test=bot.test_session(se,i+1);sess_emoji="✅"if sess_test else"❌";ss.append(sess_test);st=f"**Checking System Status...**\n\n**Checking In Progress:**\n1. {ae}\n"
        for j in range(len(bot.sessions)):
            if j<=i:em="✅"if ss[j]else"❌";st+=f"{j+2}. {em} Session {j+1}\n"
            else:st+=f"{j+2}. ⏳\n"
        await sm.edit(st);await asyncio.sleep(1)
    ws=sum(ss);ts=len(bot.sessions);ft=f"**System Status Check Completed!**\n\n1. {ae} API\n"
    for i,s in enumerate(ss):ft+=f"{i+2}. {'✅'if s else'❌'} Session {i+1}\n"
    ft+=f"\n**Summary:**\n**API:** {'Working'if api_stat else'Failed'}\n**Sessions:** {ws}/{ts} Working\n"
    if api_stat and ws>0:ft+="\n**System Is READY!**"
    else:ft+="\n**Some Issues Detected!**"
    await sm.edit(ft)

async def stats_h(e):
    uid=e.sender_id;save_user(uid)
    if uid!=ADMIN_ID:await e.reply("**You Are Not Authorized To Use This Command.**");return
    try:
        with open(users_file,'r',encoding='utf-8')as f:u=[line.strip()for line in f if line.strip()];tu=len(u)
    except:tu=0
    ut=time.time()-bot_start;h=int(ut//3600);m=int((ut%3600)//60);s=int(ut%60)
    st=f"""**Bot Statistics**

**Users:** {tu}
**Uptime:** {h}h {m}m {s}s
**Started:** {time.ctime(bot_start)}
**Sessions:** {len(bot.sessions)}
**Proxies:** {len(PROXIES_LIST)}"""
    await e.reply(st)

async def broadcast_h(e):
    uid=e.sender_id;save_user(uid)
    if uid!=ADMIN_ID:await e.reply("**You Are Not Authorized To Use This Command.**");return
    if not e.reply_to_msg_id:m=[[Button.inline("Cancel Broadcast","cancel_broadcast")]];await e.reply("**Broadcast Mode Activated**\n\n**Please Reply To A Message To Broadcast.**",buttons=m);return
    try:
        with open(users_file,'r',encoding='utf-8')as f:u=[int(line.strip())for line in f if line.strip()];tu=len(u)
        m=[[Button.inline("**Cancel Broadcast**","cancel_broadcast")]];sm=await e.reply("**Collecting Content...**",buttons=m)
        bm=await e.get_reply_message();mm=[bm];ia=False
        if bm.grouped_id:
            ia=True
            async for msg in client.iter_messages(e.chat_id,min_id=bm.id-5,max_id=bm.id+5):
                if msg.grouped_id==bm.grouped_id and msg.id!=bm.id:mm.append(msg)
        await sm.edit(f"**Collected {len(mm)} Items For Broadcast**\n**Starting Broadcast To {tu} Users...**",buttons=m)
        global broadcast_active;broadcast_active=True;sc=0;fc=0;bc=0;dc=0;oe=0
        async def update_status():
            if not broadcast_active:return
            st=f"""
**Live Broadcast Status**

**Content Items:** {len(mm)}
**Total Users:** {tu}
**Successful:** {sc}
**Failed:** {fc}
**Blocked Users:** {bc}
**Deleted Accounts:** {dc}
**Progress:** {sc+fc}/{tu}

**Click Cancel Button To Stop Broadcast**
"""
            try:await sm.edit(st,buttons=m)
            except:pass
        await update_status();cc=0
        for user_id in u:
            if not broadcast_active:break
            cc+=1
            try:
                if ia and len(mm)>1:
                    sms=[]
                    for med in mm:smsg=await client.forward_messages(user_id,med);sms.append(smsg)
                    sc+=1;sent_broadcasts[user_id]=[msg.id for msg in sms]
                else:
                    smsg=await client.forward_messages(user_id,bm);sc+=1
                    if smsg:sent_broadcasts[user_id]=[smsg.id]
            except Exception as ex:
                em=str(ex);fc+=1
                if"blocked"in em.lower():bc+=1
                elif"deactivated"in em.lower():dc+=1
                else:oe+=1
            if cc%5==0 or cc==tu:await update_status()
            await asyncio.sleep(0.2)
        if not broadcast_active:
            dp=0;td=len(sent_broadcasts)
            for uid,mids in sent_broadcasts.items():
                for mid in mids:
                    try:await client.delete_messages(uid,mid)
                    except:pass
                dp+=1
                if dp%10==0:await sm.edit(f"**Deleting Broadcasted Messages... {dp}/{td}**")
            ft=f"""
**Broadcast Cancelled**

**Partial Results:**
**Sent To:** {sc} users
**Deleted From:** {dp} users
**Stopped At:** {cc}/{tu}

**All Broadcasted Messages Have Been Deleted Successfully!**
"""
        else:
            ft=f"""
**Broadcast Completed!**

**Final Results:**
**Total Users:** {tu}
**Successful:** {sc}
**Failed:** {fc}
**Blocked Users:** {bc}
**Deleted Accounts:** {dc}
**Other Errors:** {oe}

**Success Rate:** {(sc/tu)*100:.1f}%
"""
        await sm.edit(ft);broadcast_active=False
    except Exception as ex:await e.reply(f"**Error In Broadcast: {str(ex)}**")

async def addlink_h(e):
    if e.sender_id!=ADMIN_ID:return
    cid=e.chat_id;user_states[e.sender_id]={'state':'waiting_link','chat_id':cid};await e.reply("**Send Channel Link :**")

async def process_link_h(e):
    uid=e.sender_id;cid=e.chat_id
    if uid not in user_states or user_states[uid].get('chat_id')!=cid:return
    ui=e.text.strip()
    if ui.startswith('/'):
        if uid in user_states:del user_states[uid];return
    if uid in user_states:del user_states[uid]
    global channel_link
    if ui.startswith('https://t.me/'):channel_link=ui;await e.reply("**Channel Link Updated Successfully! ✅**")
    else:await e.reply("**Invalid Link! Send Valid Telegram Channel Link.**")

async def addsession_h(e):
    if e.sender_id!=ADMIN_ID:return
    cid=e.chat_id;user_states[e.sender_id]={'state':'waiting_session','chat_id':cid};await e.reply("**Send Session ID :**")

async def process_session_h(e):
    uid=e.sender_id;cid=e.chat_id
    if uid not in user_states or user_states[uid].get('chat_id')!=cid:return
    ui=e.text.strip()
    if ui.startswith('/'):
        if uid in user_states:del user_states[uid];return
    if uid in user_states:del user_states[uid]
    try:
        se=rq.Session();se.cookies.update({'sessionid':ui})
        h={'User-Agent':'Instagram 100.0.0.17.129 Android','Content-Type':'application/x-www-form-urlencoded'}
        d={'email_or_username':'test','flow':'fxcal'};r=se.post('https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/',headers=h,data=d,timeout=10)
        if r.status_code in[200,400]:
            SESSION_IDS.append(ui);bot.sessions=bot.create_sessions();await e.reply("**Session Added Successfully! ✅**")
        else:await e.reply("**Invalid Session! Validation Failed.**")
    except:await e.reply("**Invalid Session! Validation Failed.**")

async def manage_sessions_h(e):
    if e.sender_id!=ADMIN_ID:return
    for i,sid in enumerate(SESSION_IDS,1):
        m=[[Button.inline("**Keep**",f"keep_{i}"),Button.inline("**Remove**",f"remove_{i}")]];await e.reply(f"**Session {i}:**\n`{sid}`",buttons=m)

@client.on(events.CallbackQuery(pattern=b'cancel_broadcast'))
async def cancel_broadcast_h(e):
    global broadcast_active;broadcast_active=False;await e.answer("**Broadcast Cancellation Initiated...**");await e.edit("**Cancelling Broadcast...**\n\n**Please Wait While We Stop The Broadcast And Delete Sent Messages.**")

@client.on(events.CallbackQuery(pattern=b'verify_member'))
async def verify_h(e):
    uid=e.sender_id
    if await check_member(uid):
        save_verified(uid);m=[[Button.url("🕷️𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗠𝗲","https://t.me/HloSpidey"),Button.url("𝗖𝗵𝗮𝗻𝗻𝗲𝗹🕷️",channel_link)]]
        cap="**I'M Reset Bot , By @HloSpidey**\n\n**Use My Commands:**\n/reset - Single Email / Username\n/bulk - Bulk Accounts Reset"
        try:await e.edit(cap,file='https://raw.githubusercontent.com/HloSpidey/Insta-Acc-Creater/refs/heads/main/ss.jpg',buttons=m)
        except:await e.edit(cap,buttons=m)
    else:await e.answer("You Haven'T Joined The Channel Yet!",alert=True)

@client.on(events.CallbackQuery(pattern=b'keep_(\d+)'))
async def keep_session_h(e):await e.answer("Session Kept ✅",alert=False)

@client.on(events.CallbackQuery(pattern=b'remove_(\d+)'))
async def remove_session_h(e):
    i=int(e.pattern_match.group(1))-1
    if 0<=i<len(SESSION_IDS):
        del SESSION_IDS[i];bot.sessions=bot.create_sessions();await e.answer("**Session Removed ✅**",alert=False);await e.edit(f"**Session {i+1} Removed Successfully!**")
    else:await e.answer("**Invalid Session Index**",alert=True)

print(" bot started ")
client.run_until_disconnected()
