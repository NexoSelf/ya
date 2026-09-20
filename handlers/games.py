from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from games import RPS,RPSGame,TruthDareGame,level

RPS_LABEL={RPS.ROCK:"✊ سنگ",RPS.PAPER:"📄 کاغذ",RPS.SCISSORS:"✂️ قیچی"}

def rps_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton(v,callback_data=f"rps:{k.name}") for k,v in RPS_LABEL.items()]])

def td_kind_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton("🎯 حقیقت",callback_data="tdkind:truth"),InlineKeyboardButton("🔥 جرئت",callback_data="tdkind:dare")]])

async def start_rps(update, context):
    chat=update.effective_chat; uid=update.effective_user.id
    games=context.bot_data.setdefault("rps",{})
    games[chat.id]=RPSGame(chat.id,uid)
    await update.message.reply_text("✊📄✂️ بازی سنگ کاغذ قیچی شروع شد!\nیک نفر دیگر روی دکمه زیر بزند.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🙋 شرکت در بازی",callback_data="rps_join")]]))

async def rps_callback(update,context):
    q=update.callback_query; await q.answer(); chat=q.message.chat.id; uid=q.from_user.id; games=context.bot_data.setdefault("rps",{})
    g=games.get(chat)
    if not g or g.expired(): games.pop(chat,None); return await q.edit_message_text("⏱ این بازی منقضی شد. دوباره شروع کنید.")
    if q.data=="rps_join":
        if uid==g.creator:return await q.answer("سازنده نمی‌تواند حریف خودش باشد.",show_alert=True)
        if g.opponent:return await q.answer("این بازی دو بازیکن دارد.",show_alert=True)
        g.opponent=uid; return await q.edit_message_text("بازیکن دوم وارد شد! هر دو بازیکن انتخاب خود را بزنند.",reply_markup=rps_kb())
    if q.data.startswith("rps:"):
        if uid not in (g.creator,g.opponent):return await q.answer("شما بازیکن این مسابقه نیستید.",show_alert=True)
        ok,res=g.choose(uid,RPS[q.data.split(":")[1]])
        if not ok:return await q.answer("انتخاب شما قبلاً ثبت شده.",show_alert=True)
        if res=="waiting":return await q.answer("ثبت شد؛ منتظر حریف بمان.")
        games.pop(chat,None)
        if res=="draw": return await q.edit_message_text("🤝 مساوی شد! هر دو انتخاب یکسان بود.")
        winner=g.creator if res=="creator" else g.opponent; loser=g.opponent if res=="creator" else g.creator
        db=context.application.bot_data["db"]; await db.add_points(chat,winner,30,win=True); await db.add_points(chat,loser,10)
        return await q.edit_message_text(f"🏆 برنده: {winner}\n⭐ +۳۰ امتیاز\n👏 بازنده هم +۱۰ امتیاز گرفت.")

async def start_td(update,context):
    chat=update.effective_chat
    games=context.bot_data.setdefault("td",{})
    if chat.id in games:return await update.message.reply_text("🎭 یک بازی جرئت حقیقت در این گروه در حال اجراست.")
    games[chat.id]=TruthDareGame(chat.id,[update.effective_user.id])
    await update.message.reply_text("🎭 جرئت یا حقیقت\nبازیکن‌ها با دکمه «پیوستن» وارد شوند. بعد از ورود، بازی از نفر اول شروع می‌شود.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🙋 پیوستن",callback_data="tdjoin"),InlineKeyboardButton("▶️ شروع",callback_data="tdstart")]]))

async def td_callback(update,context):
    q=update.callback_query; await q.answer(); chat=q.message.chat.id; uid=q.from_user.id; games=context.bot_data.setdefault("td",{}); g=games.get(chat)
    if not g:return
    if q.data=="tdjoin":
        if uid not in g.players:g.players.append(uid); await q.edit_message_text(f"🎭 بازیکن اضافه شد. تعداد: {len(g.players)}",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🙋 پیوستن",callback_data="tdjoin"),InlineKeyboardButton("▶️ شروع",callback_data="tdstart")]]))
        return
    if q.data=="tdstart":
        if len(g.players)<2:return await q.answer("حداقل ۲ نفر لازم است.",show_alert=True)
        return await q.edit_message_text(f"🎭 نوبت <b>کاربر {g.current}</b> است. انتخاب کن:",reply_markup=td_kind_kb(),parse_mode="HTML")
    if q.data.startswith("tdkind:"):
        if uid!=g.current:return await q.answer("الان نوبت شما نیست.",show_alert=True)
        kind=q.data.split(":")[1]; cats=await context.application.bot_data["db"].categories(); cat=cats[0]
        row=await context.application.bot_data["db"].random_question(cat["id"],kind)
        if not row:return await q.answer("برای این بخش هنوز سوالی ثبت نشده.",show_alert=True)
        await context.application.bot_data["db"].add_points(chat,uid,10,kind=kind)
        text=f"{'🎯 حقیقت' if kind=='truth' else '🔥 جرئت'}\n\n{row['text']}\n\n⭐ +۱۰ امتیاز\n\nبعد از انجام، دکمه «نفر بعد» را بزنید."
        await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➡️ نفر بعد",callback_data="tdnext")]])); return
    if q.data=="tdnext":
        if uid!=g.current:return await q.answer("فقط بازیکن فعلی می‌تواند نوبت را رد کند.",show_alert=True)
        g.next(); await q.edit_message_text(f"🎭 نوبت کاربر <b>{g.current}</b> است.",reply_markup=td_kind_kb(),parse_mode="HTML")
