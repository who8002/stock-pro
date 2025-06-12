# Fashion/Clothing Stock Bot with Inline Button, Categories, Status, Emojis, Product Image, and Admin Control

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import json, os

TOKEN = os.getenv("TOKEN")
DATA_FILE = "stock.json"
IMAGE_DIR = "images"
ADMIN_FILE = "admins.json"
CATEGORIES = {
    "T-shirt": ["Round Neck", "V-Neck"],
    "Shirt": ["Formal", "Casual"]
}

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
if not os.path.exists(ADMIN_FILE):
    with open(ADMIN_FILE, "w") as f:
        json.dump([], f)

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_admins():
    with open(ADMIN_FILE) as f:
        return json.load(f)

def save_admins(admins):
    with open(ADMIN_FILE, "w") as f:
        json.dump(admins, f, indent=2)

def is_admin(user_id):
    return user_id in load_admins()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("➕ অ্যাডমিন যোগ করুন", callback_data="add_admin")],
            [InlineKeyboardButton("➖ অ্যাডমিন রিমুভ করুন", callback_data="remove_admin")]
        ]
        await update.message.reply_text("⚙️ অ্যাডমিন কন্ট্রোল:", reply_markup=InlineKeyboardMarkup(keyboard))

    keyboard = [[InlineKeyboardButton(cat, callback_data=f"category:{cat}")] for cat in CATEGORIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 স্বাগতম! নিচে ক্যাটাগরি বাছাই করুন:", reply_markup=reply_markup)

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.split(":")[1]
    buttons = [[InlineKeyboardButton(p, callback_data=f"product:{p}")] for p in CATEGORIES[cat]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(f"🛍️ {cat} ক্যাটাগরির প্রোডাক্টগুলো:", reply_markup=reply_markup)

async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = query.data.split(":")[1]
    data = load_data()
    stock = data.get(product, 0)
    status = "🟢 যথেষ্ট আছে" if stock > 5 else "🟠 অল্প আছে" if stock > 0 else "❌ স্টকে নেই"
    path = f"{IMAGE_DIR}/{product}.jpg"
    if os.path.exists(path):
        await query.message.reply_photo(
            photo=open(path, "rb"),
            caption=f"📦 {product}\n📊 স্টক: {stock} পিচ\n{status}"
        )
    else:
        await query.message.reply_text(f"📦 {product}\n📊 স্টক: {stock} পিচ\n{status}")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ অনুমতি নেই।")
    try:
        parts = ' '.join(context.args).split('-')
        name = parts[0].strip()
        qty = int(parts[1].strip())
        data = load_data()
        data[name] = data.get(name, 0) + qty
        save_data(data)
        await update.message.reply_text(f"✅ {qty} পিচ {name} যোগ করা হয়েছে। মোট: {data[name]} পিচ।")
    except:
        await update.message.reply_text("❗ ভুল ফরম্যাট। উদাহরণ: /add T-shirt - 5")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ অনুমতি নেই।")
    try:
        parts = ' '.join(context.args).split('-')
        name = parts[0].strip()
        qty = int(parts[1].strip())
        data = load_data()
        if name not in data or data[name] < qty:
            return await update.message.reply_text("❗ যথেষ্ট স্টক নেই।")
        data[name] -= qty
        save_data(data)
        await update.message.reply_text(f"🛍️ {qty} পিচ {name} বিক্রি হয়েছে। বাকি: {data[name]} পিচ।")
    except:
        await update.message.reply_text("❗ ভুল ফরম্যাট। উদাহরণ: /sell T-shirt - 2")

async def update_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ অনুমতি নেই।")
    name = ' '.join(context.args).strip()
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        await file.download_to_drive(f"{IMAGE_DIR}/{name}.jpg")
        await update.message.reply_text(f"🖼️ {name} এর ছবি আপলোড করা হয়েছে।")
    else:
        await update.message.reply_text("❗ ছবি এবং প্রোডাক্ট নাম দিন।")

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id
    if not is_admin(user_id):
        return await query.edit_message_text("❌ অনুমতি নেই।")
    if action == "add_admin":
        context.user_data['admin_action'] = 'add'
        await query.message.reply_text("🆔 যাকে অ্যাডমিন করতে চান তার Telegram ID লিখুন:")
    elif action == "remove_admin":
        context.user_data['admin_action'] = 'remove'
        await query.message.reply_text("🆔 যাকে রিমুভ করতে চান তার Telegram ID লিখুন:")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    action = context.user_data.get('admin_action')
    if action and update.message.text.isdigit():
        admin_id = int(update.message.text)
        admins = load_admins()
        if action == 'add':
            if admin_id not in admins:
                admins.append(admin_id)
                save_admins(admins)
                await update.message.reply_text(f"✅ {admin_id} এখন অ্যাডমিন।")
            else:
                await update.message.reply_text("⚠️ এই ID আগে থেকেই অ্যাডমিন।")
        elif action == 'remove':
            if admin_id in admins:
                admins.remove(admin_id)
                save_admins(admins)
                await update.message.reply_text(f"✅ {admin_id} কে অ্যাডমিন থেকে বাদ দেওয়া হয়েছে।")
            else:
                await update.message.reply_text("⚠️ এই ID অ্যাডমিন ছিল না।")
        context.user_data.pop('admin_action', None)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("sell", sell))
app.add_handler(CommandHandler("update_image", update_image))
app.add_handler(CallbackQueryHandler(category_handler, pattern="^category:"))
app.add_handler(CallbackQueryHandler(product_handler, pattern="^product:"))
app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^(add_admin|remove_admin)$"))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_admin_input))

app.run_polling()
