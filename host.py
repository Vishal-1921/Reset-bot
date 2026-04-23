import os, requests, asyncio, json, re, random, string, subprocess, sys, time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

AID = 6
AHS = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
TOK = "8287309880:AAFTzAPlmOGr9mJl1KJWrDroyZyIq3_prSE"
ADID = 1725301348
CHL = "https://t.me/SpideyStuff"
SUP = "@HloSpidey"
app = Client("HSCMPT", api_id=AID, api_hash=AHS, bot_token=TOK)
SF, HF, UF, USF, UHCF, PUF = "stored.json", "hosted.json", "users.json", "storage.json", "hcount.json", "premium.json"
st, ht, us, stg, hct, pr, ust, rbt, tmr = {}, {}, set(), {}, {}, {}, {}, {}, {}
MXS, MXF, MXP, MXSZ = 10*1024*1024, 3, 10, 50*1024

def fs(s):
    if s<1024: return f"{s}B"
    if s<1024*1024: return f"{s/1024:.2f}KB"
    return f"{s/(1024*1024):.2f}MB"

def gid(p=""): return f"{p}{''.join(random.choices(string.ascii_lowercase+string.digits,k=10))}"
def ghid(u): return f"{u}{''.join(random.choices(string.ascii_lowercase+string.digits,k=10))}"
def ispr(u):
    u=str(u)
    if u in pr:
        if pr[u]>datetime.now().timestamp(): return 1
        del pr[u]; sv()
    return 0
def mxh(u): return MXP if ispr(u) else MXF
def val(c):
    p1=[r'API_ID\s*=\s*\d+',r'API_ID\s*=\s*["\']\d+["\']',r'api_id\s*=\s*\d+',r'api_id\s*=\s*["\']\d+["\']',r'ID\s*=\s*\d+',r'APP_ID\s*=\s*\d+',r'app_id\s*=\s*\d+']
    p2=[r'API_HASH\s*=\s*["\'][a-fA-F0-9]{32}["\']',r'api_hash\s*=\s*["\'][a-fA-F0-9]{32}["\']',r'HASH\s*=\s*["\'][a-fA-F0-9]{32}["\']',r'APP_HASH\s*=\s*["\'][a-fA-F0-9]{32}["\']',r'app_hash\s*=\s*["\'][a-fA-F0-9]{32}["\']']
    return any(re.search(p,c) for p in p1) and any(re.search(p,c) for p in p2)

def sv():
    try:
        with open(SF,'w') as f: json.dump(st,f)
        with open(HF,'w') as f: json.dump(ht,f)
        with open(UF,'w') as f: json.dump(list(us),f)
        with open(USF,'w') as f: json.dump(stg,f)
        with open(UHCF,'w') as f: json.dump(hct,f)
        with open(PUF,'w') as f: json.dump(pr,f)
    except: pass

def ld():
    global st,ht,us,stg,hct,pr
    try:
        if os.path.exists(SF):
            with open(SF,'r') as f: st=json.load(f)
        if os.path.exists(HF):
            with open(HF,'r') as f: ht=json.load(f)
        if os.path.exists(UF):
            with open(UF,'r') as f: us=set(json.load(f))
        if os.path.exists(USF):
            with open(USF,'r') as f: stg=json.load(f)
        if os.path.exists(UHCF):
            with open(UHCF,'r') as f: hct=json.load(f)
        if os.path.exists(PUF):
            with open(PUF,'r') as f: pr=json.load(f)
        return 1
    except: return 0

async def upd(u):
    us.add(str(u))
    sv()

async def chkstg(u,s):
    cu=stg.get(str(u),0)
    if cu+s>MXS: return 0,cu
    return 1,cu

async def chkht(u):
    cc=hct.get(str(u),0)
    ml=mxh(u)
    if cc>=ml: return 0,cc,ml
    return 1,cc,ml

async def clr(u,d=300):
    await asyncio.sleep(d)
    if u in ust: del ust[u]
    if u in tmr: del tmr[u]

def rbs(hi,sp,hn,oid):
    try:
        lf=f"bot_{hi}.log"
        p=subprocess.Popen([sys.executable,sp],stdout=open(lf,'w'),stderr=subprocess.STDOUT,text=True)
        rbt[hi]={'p':p,'lf':lf,'sp':sp,'hn':hn,'oid':oid,'st':datetime.now().isoformat()}
        if hi in ht: ht[hi]['st']='running'; ht[hi]['pid']=p.pid; sv()
        return 1
    except: return 0

def stp(hi):
    try:
        if hi in rbt:
            p=rbt[hi]['p']
            p.terminate()
            try: p.wait(timeout=5)
            except: p.kill()
            if hi in ht: ht[hi]['st']='stopped'; sv()
            del rbt[hi]
            return 1
    except: return 0

def stpal(uid):
    us=str(uid); s=[]
    for hi,inf in list(ht.items()):
        if inf.get('up')==us and hi in rbt:
            if stp(hi): s.append(hi)
    return s

@app.on_message(filters.command("start"))
async def stcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    nm=m.from_user.first_name or "User"
    await m.reply_photo("https://raw.githubusercontent.com/HloSpidey/photo/refs/heads/main/ss.jpg",
        caption=f"""Hey {nm} ,  I'm Files Storage + Hosting Bot 🤖🚀

🌟 **Features :
🕸️ - Free 24×7 Hosting 🚀
🕸️ - Fast Response ⚡ 
🕸️ - Store Documents, Photos, Text Messages, Not Videos 📄🖼️📝
🕸️ - Host Your Python Bot Scripts 🤖
🕸️ - Get Instant Shareable Links 🔗
🕸️ - Files Stored And Hosted In Memory, Not On Local Server Or Storage, So Don't Worry About Expl0itation ⚡🔒**

⚙️ Commands:
• /start - Show This Menu
• /store - Store A File
• /list - Show Your Stored & Hosted Files
• /get - Get Any File By ID
• /remove - Remove Your Stored Or Hosted File From Memory
• /host - Host A Python Bot Script
• /run - Run A Stopped Script
• /stop - Stop A Running Script
• /change - Change Host ID

Free Plan Hosting : Max 3 Bots
4 Free Tasks Plan : Max 10 Bots 
Contact - @HloSpidey 🕷️❤️‍🔥""",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Channel",url=CHL)]]))

@app.on_message(filters.command("admin") & filters.user(ADID))
async def admcmd(c,m):
    await m.reply("""**Admin Commands** 🕷️

/bdc <msg> - Broadcast to all
/bdcu <uid> <msg> - Msg to user
/stats - View all users
/all - Complete database
/ten <uid> - Add premium 10 days
/dismiss <uid> - Remove premium
/erase <hid> <reason> - Erase hosted script

Premium: 10 bots | Free: 3 bots""")

@app.on_message(filters.command("store"))
async def strcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    if uid in ust: del ust[uid]
    if uid in tmr: tmr[uid].cancel()
    ust[uid]="wfs"
    tmr[uid]=asyncio.create_task(clr(uid))
    await m.reply("📥 Send The File You Want To Store.\n\nSupported formats:\n• 📸 Photos\n• 📄 Documents (.zip, .py, .txt)\n• 💬 Text messages\n\nNote: Videos and Audio Files re Not Supported.")

@app.on_message(filters.command("host"))
async def hstcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    wl,cc,ml=await chkht(uid)
    if not wl:
        await m.reply(f"❌ Hosting Limit Reached !\n\nYou've hosted {cc}/{ml} scripts.\n\nMsg {SUP} To Upgrade Your Free Plan to Host 10 Bots 💎")
        return
    if uid in ust: del ust[uid]
    if uid in tmr: tmr[uid].cancel()
    ust[uid]="wfh"
    tmr[uid]=asyncio.create_task(clr(uid))
    await m.reply("📥 Send Your Python Bot Script (.py) to Host.\n\nSend Your Legit Bot Script 🤖")

@app.on_message(filters.command("get"))
async def gtcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage : `/get file_id` ")
        return
    fid=p[1].strip()
    if fid in st:
        inf=st[fid]
        adm=(uid==ADID)
        prc=await m.reply(f"📤 Sending {inf['nm']}...")
        try:
            oid=int(inf['up'])
            if inf['tp']=='doc':
                await m.reply_document(inf['fid'],caption=f"👑 Owner: <a href='tg://user?id={oid}'>{oid}</a>\n📅 Stored: {inf['ts']}")
            elif inf['tp']=='photo':
                await m.reply_photo(inf['fid'],caption=f"👑 Owner: <a href='tg://user?id={oid}'>{oid}</a>\n📅 Stored: {inf['ts']}")
            elif inf['tp']=='text':
                await m.reply(f"📝 Text\n\n{inf['cnt']}\n\n👑 Owner: <a href='tg://user?id={oid}'>{oid}</a>\n📅 Stored: {inf['ts']}")
            await prc.delete()
            if not adm and uid!=oid:
                try: await app.send_message(oid,f"🚨 User <a href='tg://user?id={uid}'>{uid}</a> got your file {inf['nm']} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                except: pass
        except: await prc.edit("❌ Failed !")
    elif fid in ht and uid==ADID:
        inf=ht[fid]
        try: await m.reply_document(inf['fid'],caption=f"📄 Hosted : {inf['nm']}\n👑 Owner : {inf['up']}\n📅 On : {inf['ts']}")
        except: await m.reply("❌ Failed !")
    else: await m.reply(f"❌ File `{fid}` Not Found  !\nUse `/list` Command")

@app.on_message(filters.command("remove"))
async def rmcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage : `/remove file_id` ")
        return
    fid=p[1].strip()
    rm=0
    if fid in st:
        inf=st[fid]
        if str(inf['up'])==str(uid) or uid==ADID:
            sz=inf['sz']
            del st[fid]
            cu=stg.get(str(uid),0)
            stg[str(uid)]=max(0,cu-sz)
            sv()
            await m.reply(f"✅ File Removed !\n📄 : {inf['nm']}\n🆔 : `{fid}`")
            rm=1
    if not rm and fid in ht:
        inf=ht[fid]
        if str(inf['up'])==str(uid) or uid==ADID:
            if fid in rbt: stp(fid)
            del ht[fid]
            cc=hct.get(str(uid),0)
            hct[str(uid)]=max(0,cc-1)
            sv()
            await m.reply(f"✅ Hosted script Removed !\n📄 : {inf['nm']}\n🆔 : `{fid}`")
            rm=1
    if not rm: await m.reply(f"❌ File `{fid}` Not Found \nUse `/list` Command To See Your Files")

@app.on_message(filters.command("erase") & filters.user(ADID))
async def erscmd(c,m):
    p=m.text.split(maxsplit=2)
    if len(p)<3:
        await m.reply("❌ Usage : `/erase host_id reason `")
        return
    hid=p[1].strip()
    rsn=p[2].strip()
    if hid not in ht:
        await m.reply(f"❌ Host ID `{hid}` Not Found !")
        return
    inf=ht[hid]
    oid=int(inf['up'])
    nm=inf['nm']
    if hid in rbt: stp(hid)
    del ht[hid]
    cc=hct.get(str(oid),0)
    hct[str(oid)]=max(0,cc-1)
    sv()
    await m.reply(f"✅ `{hid}` Stopped And Erased !")
    try: await app.send_message(oid,f"Hey <a href='tg://user?id={oid}'>{oid}</a> 👋🏻 Your File `{nm}` Has Been Stopped and Erased ⚠️\n\n🚨 Reason: {rsn}")
    except: pass

@app.on_message(filters.command("run"))
async def runcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage: `/run host_id` ")
        return
    hid=p[1].strip()
    if hid not in ht:
        await m.reply(f"❌ Host ID Not Found !")
        return
    inf=ht[hid]
    oid=int(inf['up'])
    sz=inf['sz']
    ts=inf['ts']
    if inf.get('st')=='running' or hid in rbt:
        await m.reply(f"❌ Script is Already Running !\n\nUse `/stop {hid}` First.")
        return
    sts=await m.reply("📥 Starting Your Bot...")
    try:
        sp=await app.download_media(inf['fid'])
        ok=rbs(hid,sp,inf['nm'],oid)
        if ok:
            await sts.edit(f"✅ Script Started Successfully !\n\n📄 Name : {inf['nm']}\nStatus : Running ✅\n📦 Size : {fs(sz)}\n📅 Date : {ts}\n👑 Owner : <a href='tg://user?id={oid}'>{oid}</a>\n🔧 Started By : <a href='tg://user?id={uid}'>{uid}</a>\n\nTo Stop : `/stop {hid}`")
            if uid!=oid:
                try: await app.send_message(oid,f"🚨 Your Bot Script {inf['nm']} Was Started By <a href='tg://user?id={uid}'>{uid}</a>\n📅 Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nYou Can Change Host ID To Prevent From Misuse. Send `/change {hid}`")
                except: pass
        else: await sts.edit("❌ Failed to Start Script!\n\nCheck The Script For Errors.")
    except: await sts.edit("❌ Error")

@app.on_message(filters.command("stop"))
async def stpcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage : `/stop host_id`")
        return
    hid=p[1].strip()
    if hid not in ht:
        await m.reply(f"❌ Host ID not found!")
        return
    inf=ht[hid]
    oid=int(inf['up'])
    sz=inf['sz']
    ts=inf['ts']
    if hid not in rbt:
        await m.reply(f"❌ Script is not running!")
        return
    ok=stp(hid)
    if ok:
        await m.reply(f"✅ Script Stopped Successfully!\n\n📄 Name : {inf['nm']}\nStatus : Stopped 🔴\n📦 Size : {fs(sz)}\n📅 Date : {ts}\n👑 Owner : <a href='tg://user?id={oid}'>{oid}</a>\n🔧 Stopped By : <a href='tg://user?id={uid}'>{uid}</a>")
        if uid!=oid:
            try: await app.send_message(oid,f"🚨 Your Bot Script {inf['nm']} Was Stopped By <a href='tg://user?id={uid}'>{uid}</a>\n📅 Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except: pass
    else: await m.reply("❌ Failed To Stop Script !")
@app.on_message(filters.command("change"))
async def chgcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage : `/change old_host_id` ")
        return
    old=p[1].strip()
    if old not in ht:
        await m.reply(f"❌ Host ID Not Found!")
        return
    inf=ht[old]
    if str(inf['up'])!=str(uid):
        await m.reply("❌ Only The File Owner Can Change The Host ID !")
        return
    if old in rbt:
        await m.reply("❌ Sabse Pehle Apne Iss Bot Ko Stop Kar `/stop id here` Uske Baad `/change` Command Use Kar Sakta Tu.")
        return
    new=ghid(uid)
    ht[new]=ht.pop(old)
    sv()
    await m.reply(f"✅ Changed !\n📄 {inf['nm']}\n🗑️ Old: {old}\n\n🆔 New: `{new}`")

@app.on_message(filters.command("list"))
async def lstcmd(c,m):
    uid=m.from_user.id
    await upd(uid)
    lst=[]
    lst.append("📦 Your Stored Files\n")
    uf={fid:inf for fid,inf in st.items() if str(inf['up'])==str(uid)}
    if uf:
        for fid,inf in list(uf.items())[:20]:
            tp="📄" if inf['tp']=='doc' else "📸" if inf['tp']=='photo' else "💬"
            lst.append(f"{tp} {inf['nm'][:30]} - `{fid}`")
    else: lst.append("No Stored Files.")
    lst.append("\n🐍 Your Hosted Files\n")
    uh={hid:inf for hid,inf in ht.items() if str(inf['up'])==str(uid)}
    if uh:
        for hid,inf in list(uh.items())[:20]:
            sts="✅" if inf.get('st')=='running' else "🔴"
            lst.append(f"📄 {inf['nm'][:30]} - `{hid}`")
            lst.append(f"   Status - {sts}")
    else: lst.append("No Hosted Files Found.")
    lst.append("\nUse `/store` , `/host` or `/remove` ")
    await m.reply("\n".join(lst))

@app.on_message(filters.command("stats") & filters.user(ADID))
async def statscmd(c,m):
    txt="👥 Users\n\n"
    for uid in us:
        prem="💎" if ispr(int(uid)) else "🆓"
        uf=[fid for fid,inf in st.items() if str(inf['up'])==str(uid)]
        uh=[hid for hid,inf in ht.items() if str(inf['up'])==str(uid)]
        txt+=f"👉🏻 <a href='tg://user?id={uid}'>{uid}</a> {prem}\n"
        if uf: txt+=f"- stored: {', '.join(uf[:5])}\n"
        if uh: txt+=f"- hosted: {', '.join(uh[:5])}\n"
        txt+="\n"
        if len(txt)>3500: break
    await m.reply(txt)

@app.on_message(filters.command("bdc") & filters.user(ADID))
async def bccmd(c,m):
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage : `/bdc msg` ")
        return
    msg=p[1]
    s,f=0,0
    sts=await m.reply("📢 Broadcasting...")
    for uid in us:
        try:
            await app.send_message(int(uid),f"📢 Broadcast\n\n{msg}")
            s+=1
        except: f+=1
        await asyncio.sleep(0.05)
    await sts.edit(f"✅ Sent: {s} | Failed: {f}")

@app.on_message(filters.command("bdcu") & filters.user(ADID))
async def bucmd(c,m):
    p=m.text.split(maxsplit=2)
    if len(p)<3:
        await m.reply("❌ Usage: `/bdcu user_id msg`")
        return
    try:
        uid=int(p[1])
        msg=p[2]
        await app.send_message(uid,msg)
        await m.reply(f"✅ Sent To <a href='tg://user?id={uid}'>{uid}</a>")
    except: await m.reply("❌ Failed !")

@app.on_message(filters.command("all") & filters.user(ADID))
async def allcmd(c,m):
    txt="📊 Database\n\n📦 Stored :\n"
    usd={}
    for fid,inf in st.items():
        uid=inf['up']
        if uid not in usd: usd[uid]=[]
        usd[uid].append(fid)
    for uid,fls in usd.items(): txt+=f"👤 {uid} - {len(fls)} file(s)\n"
    txt+="\n🐍 Hosted:\n"
    uhd={}
    for hid,inf in ht.items():
        uid=inf['up']
        if uid not in uhd: uhd[uid]=[]
        uhd[uid].append(hid)
    for uid,scs in uhd.items(): txt+=f"👤 {uid} - {len(scs)} script(s)\n"
    txt+=f"\n📈 Total Users: {len(us)} | Stored: `{len(st)}` | Hosted: `{len(ht)}`"
    if len(txt)>4000:
        with open("db.txt","w") as f: f.write(txt)
        await m.reply_document("db.txt",caption="Database")
        os.remove("db.txt")
    else: await m.reply(txt)

@app.on_message(filters.command("ten") & filters.user(ADID))
async def tencmd(c,m):
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage: `/ten user_id`")
        return
    try:
        uid=int(p[1])
        exp=datetime.now()+timedelta(days=10)
        pr[str(uid)]=exp.timestamp()
        sv()
        await m.reply(f"✅ <a href='tg://user?id={uid}'>{uid}</a> added to premium!")
        try: await app.send_message(uid,f"Hey <a href='tg://user?id={uid}'>User</a>, You're Now a Premium User 💎 For 10 Days ! Now You Can Host 10 Bots.")
        except: pass
    except: await m.reply("❌ Invalid ID !")

@app.on_message(filters.command("dismiss") & filters.user(ADID))
async def dscmd(c,m):
    p=m.text.split(maxsplit=1)
    if len(p)<2:
        await m.reply("❌ Usage: `/dismiss user_id` ")
        return
    try:
        uid=int(p[1])
        s=stpal(uid)
        if str(uid) in pr: del pr[str(uid)]; sv()
        await m.reply(f"✅ User removed! Stopped {len(s)} scripts.")
        try: await app.send_message(uid,"Your Premium Has Been Expired ⚠️ Your All Bots Stopped. You Can Still Host 3 Bots as Free User. Msg @HloSpidey For Free Premium 💎")
        except: pass
    except: await m.reply("❌ Invalid ID!")

@app.on_message(filters.document | filters.photo | filters.text)
async def hucmd(c,m):
    uid=m.from_user.id
    if m.text and m.text.startswith('/'): return
    if uid in ust:
        stt=ust[uid]
        if uid in tmr: tmr[uid].cancel()
        if stt=="wfs": await prsstr(c,m)
        elif stt=="wfh": await prshst(c,m)
        else: await m.reply("Timeout ⏰, Send `/store` or `/host` Again.")
    else: await m.reply("Kya Karu Iska? \n\nUse `/store` or `/host` Command First !")

async def prsstr(c,m):
    uid=m.from_user.id
    if uid in ust: del ust[uid]
    prc=await m.reply("📥 Processing...")
    try:
        sz,nm,tp,fid,cnt=0,"","","",""
        if m.document:
            f=m.document
            nm=f.file_name
            sz=f.file_size
            tp="doc"
            fid=f.file_id
            if not any(nm.lower().endswith(x) for x in ['.zip','.py','.txt']):
                await prc.edit("❌ Only .py, .zip, .txt Files are Allowed !")
                return
        elif m.photo:
            f=m.photo
            nm=f"photo_{f.file_id[:8]}.jpg"
            sz=f.file_size
            tp="photo"
            fid=f.file_id
        elif m.text:
            cnt=m.text
            sz=len(cnt.encode('utf-8'))
            nm=f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            tp="text"
        else:
            await prc.edit("❌ Unsupported !")
            return
        wl,cu=await chkstg(uid,sz)
        if not wl:
            await prc.edit(f"❌ Storage Limit !\nUsed : {fs(cu)}/{fs(MXS)}")
            return
        fid2=gid()
        st[fid2]={"fid":fid if tp!='text' else None,"cnt":cnt if tp=='text' else None,"nm":nm,"sz":sz,"tp":tp,"up":str(uid),"ts":datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        stg[str(uid)]=cu+sz
        sv()
        await prc.delete()
        await m.reply(f"✅ Stored !\n📄 {nm}\n📦 {fs(sz)}\n📅 Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🆔 File ID : `{fid2}`\n\n🔗 Share : `/get {fid2}`")
    except: await prc.edit("❌ Error !")

async def prshst(c,m):
    uid=m.from_user.id
    if uid in ust: del ust[uid]
    if not m.document or not m.document.file_name.endswith('.py'):
        await m.reply("❌ Send a Valid .py File !")
        return
    sz=m.document.file_size
    if sz>MXSZ:
        await m.reply("❌ That's Probably Encrypted  Scraping/Spam Script ! Send Legit Bot Script 🤖")
        return
    prc=await m.reply("🔍 Validating... ⏳")
    try:
        fp=await m.download()
        with open(fp,'r',encoding='utf-8',errors='ignore') as f: cnt=f.read()
        if not val(cnt):
            await prc.edit("❌ Not a Valid Bot Script ! Only Telegram Bots Scripts Allowed ✅")
            os.remove(fp); return
        wl,cc,ml=await chkht(uid)
        if not wl:
            await prc.edit(f"❌ Max Hosting Limit {cc}/{ml} ! Msg {SUP} For Free Premium 💎 To Host Max 10 Bots")
            os.remove(fp); return
        hid=ghid(uid)
        nm=m.document.file_name
        ht[hid]={"fid":m.document.file_id,"nm":nm,"sz":sz,"cnt":cnt[:500],"up":str(uid),"ts":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"st":"running"}
        hct[str(uid)]=cc+1
        sv()
        ok=rbs(hid,fp,nm,uid)
        if ok:
            await prc.edit(f"✅ Your Bot Hosted !\n📄 {nm}\n📦 {fs(sz)}\n📅 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🆔 : `{hid}`\n📊 Status : Running 🚀\n🔴 To Stop : `/stop {hid}`")
        else:
            ht[hid]['st']='stopped'; sv()
            await prc.edit(f"✅ Your Bot Hosted !\n📄 {nm}\n📦 {fs(sz)}\n📅 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🆔 : `{hid}`\n📊 Status : Stopped 🔴\n🚀 To Run : `/run {hid}`")
    except: await prc.edit("❌ Error !")

@app.on_callback_query()
async def cbcmd(c,cb):
    d=cb.data
    if d.startswith("cpy_"):
        fid=d.split("_")[1]
        await cb.answer(f"ID: {fid}",show_alert=1)
    elif d.startswith("get_"):
        fid=d.split("_")[1]
        if fid in st:
            await cb.answer("📥 Sending...",show_alert=1)
            inf=st[fid]
            oid=int(inf['up'])
            try:
                if inf['tp']=='doc':
                    await cb.message.reply_document(inf['fid'],caption=f"👑 Owner : <a href='tg://user?id={oid}'>{oid}</a>\n📅 Stored : {inf['ts']}")
                elif inf['tp']=='photo':
                    await cb.message.reply_photo(inf['fid'],caption=f"👑 Owner : <a href='tg://user?id={oid}'>{oid}</a>\n📅 Stored: {inf['ts']}")
                elif inf['tp']=='text':
                    await cb.message.reply(f"📝 {inf['cnt']}\n\n👑 Owner : <a href='tg://user?id={oid}'>{oid}</a>")
                if cb.from_user.id!=oid:
                    try: await app.send_message(oid,f"🚨 User <a href='tg://user?id={uid}'>{uid}</a> Got Your File {inf['nm']}")
                    except: pass
            except: await cb.message.reply("❌ Error")
        else: await cb.answer("Not Found !",show_alert=1)

def notify():
	requests.get(f"https://api.telegram.org/bot{TOK}/sendMessage?chat_id={ADID}&text=I'm Activated 🚀")
	
async def main():
    await app.start()
    ld()
    for hi in list(rbt.keys()): stp(hi)
    await asyncio.Event().wait()

if __name__ == "__main__":
    notify()
    app.run()
