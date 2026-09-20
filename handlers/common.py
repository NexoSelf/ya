from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_keyboard(admin=False):
    rows=[[InlineKeyboardButton("🎭 جرئت یا حقیقت",callback_data="menu_td")],[InlineKeyboardButton("✊ سنگ کاغذ قیچی",callback_data="menu_rps")],[InlineKeyboardButton("🏆 رتبه‌بندی",callback_data="menu_rank"),InlineKeyboardButton("⭐ امتیاز من",callback_data="menu_score")],[InlineKeyboardButton("ℹ️ راهنما",callback_data="menu_help")]]
    if admin: rows.append([InlineKeyboardButton("🛠 پنل مدیریت",callback_data="admin_panel")])
    return InlineKeyboardMarkup(rows)
