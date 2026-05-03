import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ========== НАСТРОЙКИ ==========
TOKEN = "8786752434:AAH7Ic141c5hQL9m5Efs8XtkMVEM-F3FVk8"
ADMIN_ID =  8101311780        # Замени на свой Telegram ID (узнать у @userinfobot)
ADMIN_USERNAME = "твой_username"  # Замени на свой username без @

DATA_FILE = "products.json"  # Файл для хранения товаров

# ========== СОСТОЯНИЯ ==========
(ENTER_NAME, ENTER_PHONE, ENTER_ADDRESS) = range(3)
(ADMIN_ADD_CAT, ADMIN_ADD_NAME, ADMIN_ADD_PRICE_R, ADMIN_ADD_PRICE_W,
 ADMIN_ADD_UNIT, ADMIN_ADD_PHOTO, ADMIN_EDIT_PRICE_R, ADMIN_EDIT_PRICE_W) = range(10, 18)

logging.basicConfig(level=logging.INFO)

# ========== ТОВАРЫ ПО УМОЛЧАНИЮ ==========
DEFAULT_PRODUCTS = {
    "wallpaper": {
        "name": "🖼 Обои",
        "items": [
            {"id": "w1", "name": "Обои виниловые однотонные",    "price_retail": 350,  "price_wholesale": 250,  "unit": "рулон", "photo": None},
            {"id": "w2", "name": "Обои флизелиновые с узором",   "price_retail": 500,  "price_wholesale": 380,  "unit": "рулон", "photo": None},
            {"id": "w3", "name": "Обои бумажные (эконом)",       "price_retail": 180,  "price_wholesale": 130,  "unit": "рулон", "photo": None},
            {"id": "w4", "name": "Фотообои 3D",                  "price_retail": 1200, "price_wholesale": 900,  "unit": "комплект", "photo": None},
            {"id": "w5", "name": "Обои текстильные",             "price_retail": 750,  "price_wholesale": 580,  "unit": "рулон", "photo": None},
            {"id": "w6", "name": "Обои под покраску",            "price_retail": 420,  "price_wholesale": 310,  "unit": "рулон", "photo": None},
        ]
    },
    "selfadhesive": {
        "name": "🪄 Самоклеящиеся обои",
        "items": [
            {"id": "sa1", "name": "Самоклейка 60x60 см однотонная",   "price_retail": 80,  "price_wholesale": 55,  "unit": "лист", "photo": None},
            {"id": "sa2", "name": "Самоклейка 60x60 см мрамор/камень","price_retail": 95,  "price_wholesale": 68,  "unit": "лист", "photo": None},
            {"id": "sa3", "name": "Самоклейка 60x60 см дерево",       "price_retail": 90,  "price_wholesale": 65,  "unit": "лист", "photo": None},
            {"id": "sa4", "name": "Самоклейка рулон 120 см x 3 м",    "price_retail": 350, "price_wholesale": 250, "unit": "рулон", "photo": None},
            {"id": "sa5", "name": "Самоклейка рулон 120 см x 5 м",    "price_retail": 550, "price_wholesale": 400, "unit": "рулон", "photo": None},
            {"id": "sa6", "name": "Самоклейка рулон 120 см x 10 м",   "price_retail": 950, "price_wholesale": 720, "unit": "рулон", "photo": None},
        ]
    },
    "tinting": {
        "name": "🌫 Самоклеящаяся тонировка",
        "items": [
            {"id": "t1", "name": "Тонировка светлая 50 см x 3 м",    "price_retail": 280, "price_wholesale": 200, "unit": "рулон", "photo": None},
            {"id": "t2", "name": "Тонировка средняя 50 см x 3 м",    "price_retail": 300, "price_wholesale": 215, "unit": "рулон", "photo": None},
            {"id": "t3", "name": "Тонировка тёмная 50 см x 3 м",     "price_retail": 300, "price_wholesale": 215, "unit": "рулон", "photo": None},
            {"id": "t4", "name": "Тонировка зеркальная 50 см x 3 м", "price_retail": 380, "price_wholesale": 280, "unit": "рулон", "photo": None},
            {"id": "t5", "name": "Тонировка матовая белая 50 см x 3 м","price_retail": 350,"price_wholesale": 260,"unit": "рулон", "photo": None},
            {"id": "t6", "name": "Тонировка рулон 100 см x 5 м",     "price_retail": 750, "price_wholesale": 560, "unit": "рулон", "photo": None},
        ]
    },
    "paint": {
        "name": "🎨 Краски",
        "items": [
            {"id": "p1", "name": "Краска водоэмульсионная белая 3 кг",  "price_retail": 380,  "price_wholesale": 280,  "unit": "банка", "photo": None},
            {"id": "p2", "name": "Краска водоэмульсионная белая 10 кг", "price_retail": 1100, "price_wholesale": 820,  "unit": "банка", "photo": None},
            {"id": "p3", "name": "Краска интерьерная цветная 3 кг",     "price_retail": 450,  "price_wholesale": 340,  "unit": "банка", "photo": None},
            {"id": "p4", "name": "Краска фасадная 10 кг",               "price_retail": 1400, "price_wholesale": 1050, "unit": "банка", "photo": None},
            {"id": "p5", "name": "Краска для потолка белая 5 кг",       "price_retail": 620,  "price_wholesale": 460,  "unit": "банка", "photo": None},
            {"id": "p6", "name": "Эмаль алкидная белая/цветная 1 кг",   "price_retail": 280,  "price_wholesale": 200,  "unit": "банка", "photo": None},
        ]
    },
    "glue": {
        "name": "🧴 Клей для обоев",
        "items": [
            {"id": "g1", "name": "Клей универсальный 250 г",          "price_retail": 120,  "price_wholesale": 85,   "unit": "пачка", "photo": None},
            {"id": "g2", "name": "Клей для флизелина 500 г",          "price_retail": 220,  "price_wholesale": 160,  "unit": "пачка", "photo": None},
            {"id": "g3", "name": "Клей виниловый 500 г",              "price_retail": 200,  "price_wholesale": 150,  "unit": "пачка", "photo": None},
            {"id": "g4", "name": "Клей усиленный тяжёлые обои 500 г", "price_retail": 260,  "price_wholesale": 190,  "unit": "пачка", "photo": None},
            {"id": "g5", "name": "Клей оптом упаковка 10 пачек",      "price_retail": 1800, "price_wholesale": 1300, "unit": "упаковка", "photo": None},
        ]
    },
    "tools": {
        "name": "🖌 Валики и инструменты",
        "items": [
            {"id": "r1", "name": "Валик поролоновый 18 см",         "price_retail": 120, "price_wholesale": 85,  "unit": "шт", "photo": None},
            {"id": "r2", "name": "Валик велюровый 18 см",           "price_retail": 180, "price_wholesale": 130, "unit": "шт", "photo": None},
            {"id": "r3", "name": "Валик прижимной для обоев 10 см", "price_retail": 90,  "price_wholesale": 65,  "unit": "шт", "photo": None},
            {"id": "r4", "name": "Кисть малярная 50 мм",            "price_retail": 80,  "price_wholesale": 55,  "unit": "шт", "photo": None},
            {"id": "r5", "name": "Кисть радиаторная для батарей",   "price_retail": 110, "price_wholesale": 80,  "unit": "шт", "photo": None},
            {"id": "r6", "name": "Шпатель металлический 10 см",     "price_retail": 70,  "price_wholesale": 50,  "unit": "шт", "photo": None},
            {"id": "r7", "name": "Шпатель металлический 30 см",     "price_retail": 130, "price_wholesale": 95,  "unit": "шт", "photo": None},
            {"id": "r8", "name": "Малярный скотч 50 м",             "price_retail": 60,  "price_wholesale": 40,  "unit": "рулон", "photo": None},
            {"id": "r9", "name": "Малярная плёнка защитная",        "price_retail": 150, "price_wholesale": 110, "unit": "рулон", "photo": None},
        ]
    },
    "primer": {
        "name": "🪣 Грунтовка и шпаклёвка",
        "items": [
            {"id": "pr1", "name": "Грунтовка универсальная 5 л",            "price_retail": 480,  "price_wholesale": 360, "unit": "канистра", "photo": None},
            {"id": "pr2", "name": "Грунтовка глубокого проникновения 10 л", "price_retail": 850,  "price_wholesale": 640, "unit": "канистра", "photo": None},
            {"id": "pr3", "name": "Шпаклёвка финишная 5 кг",                "price_retail": 350,  "price_wholesale": 260, "unit": "ведро", "photo": None},
            {"id": "pr4", "name": "Шпаклёвка финишная 20 кг",               "price_retail": 1100, "price_wholesale": 820, "unit": "мешок", "photo": None},
            {"id": "pr5", "name": "Шпаклёвка стартовая 20 кг",              "price_retail": 900,  "price_wholesale": 670, "unit": "мешок", "photo": None},
        ]
    },
}

# ========== РАБОТА С ДАННЫМИ ==========

def load_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_products(DEFAULT_PRODUCTS)
    return DEFAULT_PRODUCTS

def save_products(products):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def find_item(products, cat_key, item_id):
    return next((i for i in products[cat_key]["items"] if i["id"] == item_id), None)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_cart(context):
    if "cart" not in context.user_data:
        context.user_data["cart"] = []
    return context.user_data["cart"]

def get_mode(context):
    return context.user_data.get("mode", "retail")

def format_cart(cart, mode):
    if not cart:
        return "🛒 Корзина пуста"
    text = "🛒 *Ваша корзина:*\n\n"
    total = 0
    for i, item in enumerate(cart, 1):
        price = item["price_wholesale"] if mode == "wholesale" else item["price_retail"]
        subtotal = price * item["qty"]
        total += subtotal
        text += f"{i}. {item['name']}\n   {item['qty']} {item['unit']} x {price} сом = *{subtotal} сом*\n"
    text += f"\n💰 *Итого: {total} сом*"
    text += "\n_(оптовые цены)_" if mode == "wholesale" else "\n_(розничные цены)_"
    return text

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Обои",               callback_data="cat_wallpaper"),
         InlineKeyboardButton("🪄 Самоклейка",         callback_data="cat_selfadhesive")],
        [InlineKeyboardButton("🌫 Тонировка",          callback_data="cat_tinting"),
         InlineKeyboardButton("🎨 Краски",             callback_data="cat_paint")],
        [InlineKeyboardButton("🧴 Клей",               callback_data="cat_glue"),
         InlineKeyboardButton("🖌 Валики/инструменты", callback_data="cat_tools")],
        [InlineKeyboardButton("🪣 Грунтовка/шпаклёвка", callback_data="cat_primer")],
        [InlineKeyboardButton("🛒 Корзина",            callback_data="cart"),
         InlineKeyboardButton("📦 Опт / Розница",      callback_data="toggle_mode")],
        [InlineKeyboardButton("📞 Контакты",           callback_data="contacts")]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить товар",    callback_data="adm_add")],
        [InlineKeyboardButton("✏️ Изменить цену",     callback_data="adm_edit_cat")],
        [InlineKeyboardButton("🗑 Удалить товар",     callback_data="adm_del_cat")],
        [InlineKeyboardButton("🖼 Добавить фото",     callback_data="adm_photo_cat")],
        [InlineKeyboardButton("🏠 Главная",           callback_data="back_main")]
    ])

def categories_keyboard(prefix):
    products = load_products()
    buttons = []
    row = []
    for i, (key, cat) in enumerate(products.items()):
        row.append(InlineKeyboardButton(cat["name"], callback_data=f"{prefix}_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin")])
    return InlineKeyboardMarkup(buttons)

def is_admin(user_id):
    return user_id == ADMIN_ID


# ========== СТАРТ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = get_mode(context)
    mode_text = "🏪 Режим: *Розница*" if mode == "retail" else "📦 Режим: *Опт*"
    text = (
        f"👋 Добро пожаловать в магазин *Oboi Exclusive KG*!\n\n"
        f"У нас есть всё для ремонта:\n"
        f"обои, самоклейка, тонировка, краски,\n"
        f"клей, валики, грунтовка и многое другое!\n\n"
        f"{mode_text}\n\nВыберите категорию:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


# ========== АДМИН ПАНЕЛЬ ==========

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет доступа.")
        return
    await update.message.reply_text(
        "🔧 *Админ-панель*\n\nЧто хотите сделать?",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("❌ Нет доступа", show_alert=True)
        return
    await query.edit_message_text(
        "🔧 *Админ-панель*\n\nЧто хотите сделать?",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )

# --- Добавить товар ---
async def adm_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *Добавить товар*\n\nВыберите категорию:",
        parse_mode="Markdown",
        reply_markup=categories_keyboard("adm_add_cat")
    )

async def adm_add_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_key = query.data.replace("adm_add_cat_", "")
    context.user_data["adm_cat"] = cat_key
    await query.edit_message_text(
        f"➕ Введите *название товара*:",
        parse_mode="Markdown"
    )
    return ADMIN_ADD_NAME

async def adm_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["adm_name"] = update.message.text
    await update.message.reply_text("💰 Введите *розничную цену* (число в сомах):", parse_mode="Markdown")
    return ADMIN_ADD_PRICE_R

async def adm_add_price_r(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["adm_price_r"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите число! Попробуйте ещё раз:")
        return ADMIN_ADD_PRICE_R
    await update.message.reply_text("📦 Введите *оптовую цену* (число в сомах):", parse_mode="Markdown")
    return ADMIN_ADD_PRICE_W

async def adm_add_price_w(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["adm_price_w"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите число! Попробуйте ещё раз:")
        return ADMIN_ADD_PRICE_W
    await update.message.reply_text("📏 Введите *единицу измерения* (рулон / шт / банка / пачка и т.д.):", parse_mode="Markdown")
    return ADMIN_ADD_UNIT

async def adm_add_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["adm_unit"] = update.message.text
    await update.message.reply_text(
        "🖼 Отправьте *фото товара* (или напишите «нет» чтобы пропустить):",
        parse_mode="Markdown"
    )
    return ADMIN_ADD_PHOTO

async def adm_add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    cat_key = context.user_data["adm_cat"]
    cat = products[cat_key]

    # Генерируем новый ID
    existing_ids = [i["id"] for i in cat["items"]]
    new_id = f"{cat_key[:2]}{len(existing_ids)+1}"
    while new_id in existing_ids:
        new_id += "x"

    photo_id = None
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id

    new_item = {
        "id": new_id,
        "name": context.user_data["adm_name"],
        "price_retail": context.user_data["adm_price_r"],
        "price_wholesale": context.user_data["adm_price_w"],
        "unit": context.user_data["adm_unit"],
        "photo": photo_id
    }
    cat["items"].append(new_item)
    save_products(products)

    await update.message.reply_text(
        f"✅ Товар *{new_item['name']}* добавлен в категорию *{cat['name']}*!",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    return ConversationHandler.END

# --- Изменить цену ---
async def adm_edit_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✏️ *Изменить цену*\n\nВыберите категорию:",
        parse_mode="Markdown", reply_markup=categories_keyboard("adm_edit_item_cat"))

async def adm_edit_item_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_key = query.data.replace("adm_edit_item_cat_", "")
    context.user_data["adm_cat"] = cat_key
    products = load_products()
    cat = products[cat_key]
    buttons = [[InlineKeyboardButton(i["name"], callback_data=f"adm_edit_item_{cat_key}_{i['id']}")]
               for i in cat["items"]]
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="adm_edit_cat")])
    await query.edit_message_text(f"✏️ Выберите товар для редактирования:",
        reply_markup=InlineKeyboardMarkup(buttons))

async def adm_edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    cat_key = parts[3]
    item_id = "_".join(parts[4:])
    context.user_data["adm_cat"] = cat_key
    context.user_data["adm_item_id"] = item_id
    products = load_products()
    item = find_item(products, cat_key, item_id)
    await query.edit_message_text(
        f"✏️ *{item['name']}*\n\n"
        f"Розничная: {item['price_retail']} сом\n"
        f"Оптовая: {item['price_wholesale']} сом\n\n"
        f"Введите новую *розничную цену*:",
        parse_mode="Markdown"
    )
    return ADMIN_EDIT_PRICE_R

async def adm_edit_price_r(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["adm_price_r"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите число:")
        return ADMIN_EDIT_PRICE_R
    await update.message.reply_text("📦 Введите новую *оптовую цену*:", parse_mode="Markdown")
    return ADMIN_EDIT_PRICE_W

async def adm_edit_price_w(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_price_w = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите число:")
        return ADMIN_EDIT_PRICE_W
    products = load_products()
    cat_key = context.user_data["adm_cat"]
    item_id = context.user_data["adm_item_id"]
    item = find_item(products, cat_key, item_id)
    item["price_retail"] = context.user_data["adm_price_r"]
    item["price_wholesale"] = new_price_w
    save_products(products)
    await update.message.reply_text(
        f"✅ Цены на *{item['name']}* обновлены!\n"
        f"Розница: {item['price_retail']} сом\n"
        f"Опт: {item['price_wholesale']} сом",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    return ConversationHandler.END

# --- Удалить товар ---
async def adm_del_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🗑 *Удалить товар*\n\nВыберите категорию:",
        parse_mode="Markdown", reply_markup=categories_keyboard("adm_del_item_cat"))

async def adm_del_item_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_key = query.data.replace("adm_del_item_cat_", "")
    products = load_products()
    cat = products[cat_key]
    buttons = [[InlineKeyboardButton(f"🗑 {i['name']}", callback_data=f"adm_del_item_{cat_key}_{i['id']}")]
               for i in cat["items"]]
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="adm_del_cat")])
    await query.edit_message_text("🗑 Выберите товар для удаления:",
        reply_markup=InlineKeyboardMarkup(buttons))

async def adm_del_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    cat_key = parts[3]
    item_id = "_".join(parts[4:])
    products = load_products()
    item = find_item(products, cat_key, item_id)
    name = item["name"]
    products[cat_key]["items"] = [i for i in products[cat_key]["items"] if i["id"] != item_id]
    save_products(products)
    await query.edit_message_text(
        f"✅ Товар *{name}* удалён!",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )

# --- Добавить фото ---
async def adm_photo_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🖼 *Добавить/изменить фото*\n\nВыберите категорию:",
        parse_mode="Markdown", reply_markup=categories_keyboard("adm_photo_item_cat"))

async def adm_photo_item_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_key = query.data.replace("adm_photo_item_cat_", "")
    context.user_data["adm_cat"] = cat_key
    products = load_products()
    cat = products[cat_key]
    buttons = [[InlineKeyboardButton(
        f"{'✅' if i.get('photo') else '❌'} {i['name']}",
        callback_data=f"adm_photo_item_{cat_key}_{i['id']}"
    )] for i in cat["items"]]
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="adm_photo_cat")])
    await query.edit_message_text("🖼 Выберите товар (✅ = есть фото, ❌ = нет фото):",
        reply_markup=InlineKeyboardMarkup(buttons))

async def adm_photo_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    cat_key = parts[3]
    item_id = "_".join(parts[4:])
    context.user_data["adm_cat"] = cat_key
    context.user_data["adm_item_id"] = item_id
    products = load_products()
    item = find_item(products, cat_key, item_id)
    await query.edit_message_text(
        f"🖼 *{item['name']}*\n\nОтправьте фото товара:",
        parse_mode="Markdown"
    )
    return ADMIN_ADD_PHOTO

async def adm_save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Отправьте фото! Попробуйте ещё раз:")
        return ADMIN_ADD_PHOTO
    photo_id = update.message.photo[-1].file_id
    products = load_products()
    cat_key = context.user_data["adm_cat"]
    item_id = context.user_data["adm_item_id"]
    item = find_item(products, cat_key, item_id)
    item["photo"] = photo_id
    save_products(products)
    await update.message.reply_text(
        f"✅ Фото для *{item['name']}* сохранено!",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    return ConversationHandler.END


# ========== МАГАЗИН (КЛИЕНТ) ==========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    mode = get_mode(context)
    products = load_products()

    if data == "admin":
        await admin_panel(update, context)
        return

    # --- Категория ---
    if data.startswith("cat_"):
        cat_key = data.replace("cat_", "")
        cat = products[cat_key]
        buttons = []
        for item in cat["items"]:
            price = item["price_wholesale"] if mode == "wholesale" else item["price_retail"]
            buttons.append([InlineKeyboardButton(
                f"{item['name']} — {price} сом/{item['unit']}",
                callback_data=f"item_{cat_key}_{item['id']}"
            )])
        buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])
        await query.edit_message_text(
            f"{cat['name']}\n\n{'📦 Оптовые цены' if mode == 'wholesale' else '🏪 Розничные цены'}:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # --- Товар ---
    elif data.startswith("item_"):
        parts = data.split("_")
        cat_key = parts[1]
        item_id = "_".join(parts[2:])
        item = find_item(products, cat_key, item_id)
        price = item["price_wholesale"] if mode == "wholesale" else item["price_retail"]
        caption = (
            f"*{item['name']}*\n\n"
            f"💰 Цена: *{price} сом* / {item['unit']}\n"
            f"{'📦 Оптовая цена' if mode == 'wholesale' else '🏪 Розничная цена'}\n\n"
            f"Выберите количество:"
        )
        buttons = [
            [InlineKeyboardButton("1",  callback_data=f"add_{cat_key}_{item_id}_1"),
             InlineKeyboardButton("3",  callback_data=f"add_{cat_key}_{item_id}_3"),
             InlineKeyboardButton("5",  callback_data=f"add_{cat_key}_{item_id}_5")],
            [InlineKeyboardButton("10", callback_data=f"add_{cat_key}_{item_id}_10"),
             InlineKeyboardButton("20", callback_data=f"add_{cat_key}_{item_id}_20"),
             InlineKeyboardButton("50", callback_data=f"add_{cat_key}_{item_id}_50")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"cat_{cat_key}")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        if item.get("photo"):
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=item["photo"],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            await query.edit_message_text(caption, parse_mode="Markdown", reply_markup=markup)

    # --- Добавить в корзину ---
    elif data.startswith("add_"):
        parts = data.split("_")
        cat_key = parts[1]
        qty = int(parts[-1])
        item_id = "_".join(parts[2:-1])
        item = find_item(products, cat_key, item_id)
        cart = get_cart(context)
        existing = next((c for c in cart if c["id"] == item_id), None)
        if existing:
            existing["qty"] += qty
        else:
            cart.append({
                "id": item_id,
                "name": item["name"],
                "price_retail": item["price_retail"],
                "price_wholesale": item["price_wholesale"],
                "unit": item["unit"],
                "qty": qty
            })
        text = f"✅ *{item['name']}* — {qty} {item['unit']} добавлено!\n\n" + format_cart(cart, mode)
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Ещё в эту категорию", callback_data=f"cat_{cat_key}")],
            [InlineKeyboardButton("🛒 Корзина", callback_data="cart"),
             InlineKeyboardButton("🏠 Главная",  callback_data="back_main")]
        ])
        try:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)

    # --- Корзина ---
    elif data == "cart":
        cart = get_cart(context)
        text = format_cart(cart, mode)
        buttons = []
        if cart:
            buttons.append([InlineKeyboardButton("✅ Оформить заказ",  callback_data="checkout")])
            buttons.append([InlineKeyboardButton("🗑 Очистить корзину", callback_data="clear_cart")])
        buttons.append([InlineKeyboardButton("🏠 Главная", callback_data="back_main")])
        try:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        except Exception:
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    # --- Очистить корзину ---
    elif data == "clear_cart":
        context.user_data["cart"] = []
        await query.edit_message_text("🗑 Корзина очищена.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главная", callback_data="back_main")]]))

    # --- Переключить опт/розница ---
    elif data == "toggle_mode":
        current = get_mode(context)
        new_mode = "wholesale" if current == "retail" else "retail"
        context.user_data["mode"] = new_mode
        mode_text = "📦 Режим: *Опт*" if new_mode == "wholesale" else "🏪 Режим: *Розница*"
        await query.edit_message_text(f"{mode_text}\n\nВыберите категорию:",
            parse_mode="Markdown", reply_markup=main_menu_keyboard())

    # --- Контакты ---
    elif data == "contacts":
        await query.edit_message_text(
            "📞 *Контакты магазина Oboi Exclusive KG*\n\n"
            "📱 Телефон: +996 990606366\n"
            "💬 WhatsApp: +996 550105210\n"
            "📍 Адрес: г. Ош, ул.Татан\n"
            "🕐 Режим работы: Пн–Сб 9:00–18:00",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главная", callback_data="back_main")]]))

    # --- Главная ---
    elif data == "back_main":
        mode_text = "🏪 Режим: *Розница*" if mode == "retail" else "📦 Режим: *Опт*"
        try:
            await query.edit_message_text(
                f"🏠 Главное меню\n\n{mode_text}\n\nВыберите категорию:",
                parse_mode="Markdown", reply_markup=main_menu_keyboard())
        except Exception:
            await query.message.reply_text(
                f"🏠 Главное меню\n\n{mode_text}\n\nВыберите категорию:",
                parse_mode="Markdown", reply_markup=main_menu_keyboard())

    # --- Оформить заказ ---
    elif data == "checkout":
        cart = get_cart(context)
        if not cart:
            await query.edit_message_text("🛒 Корзина пуста!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главная", callback_data="back_main")]]))
            return
        try:
            await query.edit_message_text(
                "📝 *Оформление заказа*\n\nШаг 1 из 3\n\nВведите ваше *имя*:",
                parse_mode="Markdown")
        except Exception:
            await query.message.reply_text(
                "📝 *Оформление заказа*\n\nШаг 1 из 3\n\nВведите ваше *имя*:",
                parse_mode="Markdown")
        return ENTER_NAME


# ========== ОФОРМЛЕНИЕ ЗАКАЗА ==========

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_name"] = update.message.text
    await update.message.reply_text("📝 Шаг 2 из 3\n\n📱 Введите ваш *номер телефона*:", parse_mode="Markdown")
    return ENTER_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_phone"] = update.message.text
    await update.message.reply_text(
        "📝 Шаг 3 из 3\n\n📍 Введите *адрес доставки*\n_(или напишите «Самовывоз»)_:",
        parse_mode="Markdown")
    return ENTER_ADDRESS

async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = get_cart(context)
    mode = get_mode(context)
    name    = context.user_data.get("order_name")
    phone   = context.user_data.get("order_phone")
    address = update.message.text
    user    = update.effective_user

    cart_text = format_cart(cart, mode)

    # Клиенту — подтверждение + кнопка написать продавцу
    await update.message.reply_text(
        f"✅ *Заказ принят!*\n\n"
        f"👤 Имя: {name}\n"
        f"📱 Телефон: {phone}\n"
        f"📍 Адрес: {address}\n\n"
        + cart_text +
        "\n\n⏳ Нажмите кнопку ниже чтобы написать продавцу и подтвердить заказ:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Написать продавцу", url=f"https://t.me/{ADMIN_USERNAME}")],
            [InlineKeyboardButton("🏠 Главная", callback_data="back_main")]
        ])
    )

    # Уведомление администратору
    admin_text = (
        f"🔔 *НОВЫЙ ЗАКАЗ!*\n\n"
        f"👤 {name}\n"
        f"📱 {phone}\n"
        f"📍 {address}\n"
        f"📦 Тип: {'Опт' if mode == 'wholesale' else 'Розница'}\n"
        f"🆔 Telegram: @{user.username or 'нет username'} (ID: {user.id})\n\n"
        + cart_text
    )
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Написать клиенту", url=f"tg://user?id={user.id}")]
            ])
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить уведомление: {e}")

    context.user_data["cart"] = []
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оформление отменено.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


# ========== ЗАПУСК ==========

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Диалог оформления заказа
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^checkout$")],
        states={
            ENTER_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            ENTER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Диалог добавления товара (админ)
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adm_add_cat, pattern="^adm_add_cat_")],
        states={
            ADMIN_ADD_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_add_name)],
            ADMIN_ADD_PRICE_R: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_add_price_r)],
            ADMIN_ADD_PRICE_W: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_add_price_w)],
            ADMIN_ADD_UNIT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_add_unit)],
            ADMIN_ADD_PHOTO:   [
                MessageHandler(filters.PHOTO, adm_add_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, adm_add_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Диалог изменения цены (админ)
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adm_edit_item, pattern="^adm_edit_item_")],
        states={
            ADMIN_EDIT_PRICE_R: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_edit_price_r)],
            ADMIN_EDIT_PRICE_W: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_edit_price_w)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Диалог добавления фото (админ)
    photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adm_photo_item, pattern="^adm_photo_item_")],
        states={
            ADMIN_ADD_PHOTO: [MessageHandler(filters.PHOTO, adm_save_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(order_conv)
    app.add_handler(add_conv)
    app.add_handler(edit_conv)
    app.add_handler(photo_conv)
    app.add_handler(CallbackQueryHandler(adm_add,          pattern="^adm_add$"))
    app.add_handler(CallbackQueryHandler(adm_edit_cat,     pattern="^adm_edit_cat$"))
    app.add_handler(CallbackQueryHandler(adm_edit_item_cat,pattern="^adm_edit_item_cat_"))
    app.add_handler(CallbackQueryHandler(adm_del_cat,      pattern="^adm_del_cat$"))
    app.add_handler(CallbackQueryHandler(adm_del_item_cat, pattern="^adm_del_item_cat_"))
    app.add_handler(CallbackQueryHandler(adm_del_item,     pattern="^adm_del_item_"))
    app.add_handler(CallbackQueryHandler(adm_photo_cat,    pattern="^adm_photo_cat$"))
    app.add_handler(CallbackQueryHandler(adm_photo_item_cat,pattern="^adm_photo_item_cat_"))
    app.add_handler(CallbackQueryHandler(admin_panel,      pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()