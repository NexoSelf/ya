import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import load_settings
from database import Database
from handlers.common import main_keyboard
from handlers.games import start_rps,rps_callback,start_td,td_callback
from handlers.admin import panel as admin_panel,callback as admin_callback,admin_text,is_admin
from games import level

logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s',level=logging.INFO)

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await context.application.bot_data['db'].upsert_user(update.effective_user)
    admin=is_admin(update.effective_user.id,context.application.bot_data['settings'])
    await update.message.reply_text("🎉 به Y & A خوش اومدی!\n\nاز منوی زیر بازی رو انتخاب کن:",reply_markup=main_keyboard(admin))

async def text(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:return
    if await admin_text(update,context):return
    t=update.message.text.strip().lower()
    db=context.application.bot_data['db']; chat=update.effective_chat; uid=update.effective_user.id
    await db.upsert_user(update.effective_user)
    if t in ('استارت','شروع','start'):
        return await start(update,context)
    if t in ('بازی','بازی ها','بازی‌ها'): return await update.message.reply_text("🎮 بازی‌ها:",reply_markup=main_keyboard(is_admin(uid,context.application.bot_data['settings'])))
    if t in ('جرئت حقیقت','جرئت یا حقیقت','جرات حقیقت','حقیقت جرئت'): return await start_td(update,context)
    if t in ('سنگ کاغذ قیچی','سنگ کاغذ قیچی دو نفره'): return await start_rps(update,context)
    if t in ('امتیاز','امتیاز من'):
        s=await db.score(chat.id,uid); return await update.message.reply_text(f"⭐ امتیاز شما: {s['points']}\n🏅 سطح: {level(s['points'])}\n🏆 برد: {s['wins']}")
    if t in ('رتبه بندی','رتبه‌بندی','رنک','برترین‌ها'):
        rows=await db.leaderboard(chat.id); lines=[f"{i}. {r['first_name'] or r['username'] or r['user_id']} — ⭐ {r['points']} — سطح {level(r['points'])}" for i,r in enumerate(rows,1)]; return await update.message.reply_text("🏆 رتبه‌بندی گروه\n\n"+('\n'.join(lines) if lines else 'هنوز امتیازی ثبت نشده.'))
    if t in ('راهنما','کمک'):
        return await update.message.reply_text("ℹ️ راهنما\n\nجرئت حقیقت — بازی نوبتی\nسنگ کاغذ قیچی — بازی دونفره\nامتیاز — امتیاز و سطح\nرتبه بندی — جدول گروه")
    if t in ('پنل مدیریت','مدیریت') and is_admin(uid,context.application.bot_data['settings']): return await admin_panel(update,context)

async def buttons(update,context):
    q=update.callback_query
    if q.data.startswith('rps'):
        return await rps_callback(update,context)
    if q.data.startswith('td'):
        return await td_callback(update,context)
    if q.data.startswith('admin'):
        return await admin_callback(update,context)
    await q.answer()
    if q.data=='menu_td': return await q.message.reply_text('🎭 جرئت یا حقیقت را در گروه شروع کنید.',reply_markup=main_keyboard())
    if q.data=='menu_rps': return await q.message.reply_text('✊ سنگ کاغذ قیچی را در گروه شروع کنید.')
    if q.data=='menu_help': return await q.message.reply_text('ℹ️ دستورها: جرئت حقیقت، سنگ کاغذ قیچی، امتیاز، رتبه بندی')
    if q.data=='menu_score':
        s=await context.application.bot_data['db'].score(q.message.chat.id,q.from_user.id); return await q.message.reply_text(f"⭐ {s['points']} امتیاز | 🏅 سطح {level(s['points'])}")
    if q.data=='menu_rank':
        rows=await context.application.bot_data['db'].leaderboard(q.message.chat.id); return await q.message.reply_text('\n'.join(f"{i}. {r['first_name']} — {r['points']}⭐" for i,r in enumerate(rows,1)) or 'خالی است.')

async def post_init(app):
    settings=app.bot_data['settings']; app.bot_data['db']=Database(settings.db_path); db=await app.bot_data['db'].connect(); await db.close(); logging.info('Y&A ready')

def build_app():
    settings=load_settings(); app=Application.builder().token(settings.bot_token).post_init(post_init).build(); app.bot_data['settings']=settings
    app.add_handler(CommandHandler('start',start)); app.add_handler(CallbackQueryHandler(buttons)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text)); return app

if __name__=='__main__': build_app().run_polling(allowed_updates=Update.ALL_TYPES)
