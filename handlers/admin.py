from telegram import InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ConversationHandler
WAIT_CAT=1; WAIT_Q=2

def is_admin(uid,settings): return uid in settings.admin_ids

async def panel(update,context):
    q=update.callback_query
    if q: await q.answer(); msg=q.message
    else: msg=update.message
    if not is_admin(msg.chat.id if False else (q.from_user.id if q else update.effective_user.id),context.application.bot_data['settings']): return
    db=context.application.bot_data['db']; u,c,qs=await db.stats()
    await msg.reply_text(f"🛠 پنل مدیریت\n\n👤 کاربران: {u}\n👥 گروه‌ها: {c}\n❓ سوال‌ها: {qs}",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ دسته جدید",callback_data="admin_addcat"),InlineKeyboardButton("➕ سوال جدید",callback_data="admin_addq")],[InlineKeyboardButton("📚 دسته‌ها",callback_data="admin_cats")]]))

async def callback(update,context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id; settings=context.application.bot_data['settings']
    if not is_admin(uid,settings):return await q.answer("دسترسی ندارید.",show_alert=True)
    if q.data=="admin_addcat": context.user_data['admin_state']='cat'; return await q.message.reply_text("نام دسته را ارسال کنید:")
    if q.data=="admin_addq":
        cats=await context.application.bot_data['db'].categories(); context.user_data['admin_state']='q'; context.user_data['cats']=[(r['id'],r['name']) for r in cats]; return await q.message.reply_text("فرمت سوال:\nشناسه‌دسته | حقیقت/جرئت | متن سوال\nمثال: 1 | حقیقت | بهترین خاطره‌ات چیست؟")
    if q.data=="admin_cats":
        cats=await context.application.bot_data['db'].categories(); return await q.message.reply_text("📚 دسته‌ها:\n"+"\n".join(f"{r['id']} — {r['name']}" for r in cats))

async def admin_text(update,context):
    if not is_admin(update.effective_user.id,context.application.bot_data['settings']):return False
    state=context.user_data.get('admin_state'); db=context.application.bot_data['db']; text=update.message.text.strip()
    if state=='cat':
        ok=await db.add_category(text); context.user_data.pop('admin_state',None); await update.message.reply_text("✅ دسته اضافه شد." if ok else "❌ این دسته از قبل وجود دارد."); return True
    if state=='q':
        parts=[x.strip() for x in text.split('|',2)]
        if len(parts)!=3 or not parts[0].isdigit() or parts[1] not in ('حقیقت','جرئت'):
            await update.message.reply_text("❌ فرمت نادرست است. مثال: 1 | حقیقت | متن سوال"); return True
        await db.add_question(int(parts[0]),'truth' if parts[1]=='حقیقت' else 'dare',parts[2]); context.user_data.pop('admin_state',None); await update.message.reply_text("✅ سوال اضافه شد."); return True
    return False
