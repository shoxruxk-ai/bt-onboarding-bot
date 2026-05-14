"""
Baker Tilly Tashkent — Onboarding Bot
Telegram + Gemini 2.0 Flash via direct HTTP (no Google SDK)
"""

import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ── Config ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.0-flash:generateContent"
    f"?key={GEMINI_API_KEY}"
)

# ── Topics & Questions ────────────────────────────────────────────────────────
TOPICS = {
    "ru": [
        ("📋 Трудовой распорядок",   "rules"),
        ("⚖️ Кодекс этики",          "ethics"),
        ("🏖️ Отпуска и больничные",  "hr"),
        ("📈 Карьерная лестница",     "career"),
        ("🎯 Испытательный срок",     "probation"),
        ("💻 IT и инструменты",       "it"),
        ("🤝 Корпоративная культура", "culture"),
        ("📚 Обучение и развитие",    "training"),
    ],
    "uz": [
        ("📋 Mehnat tartibi",          "rules"),
        ("⚖️ Axloq kodeksi",          "ethics"),
        ("🏖️ Ta'til va kasallik",     "hr"),
        ("📈 Martaba zinapoyasi",      "career"),
        ("🎯 Sinov muddati",           "probation"),
        ("💻 IT va vositalar",         "it"),
        ("🤝 Korporativ madaniyat",    "culture"),
        ("📚 O'qitish va rivojlanish", "training"),
    ],
}

TOPIC_QUESTIONS = {
    "ru": {
        "rules":     "Расскажи о правилах внутреннего трудового распорядка: рабочее время, дресс-код, посещаемость",
        "ethics":    "Расскажи о кодексе профессиональной этики аудитора",
        "hr":        "Как оформить отпуск или больничный? Какие документы нужны?",
        "career":    "Какая карьерная лестница в Baker Tilly Tashkent? Как продвигаться?",
        "probation": "Как проходит испытательный срок? Что от меня ожидают?",
        "it":        "Какие IT-инструменты используются? Как получить доступы?",
        "culture":   "Расскажи о корпоративной культуре и ценностях компании",
        "training":  "Какие возможности для обучения, сертификаций и профессионального развития?",
    },
    "uz": {
        "rules":     "Ichki mehnat tartibi qoidalari haqida aytib bering",
        "ethics":    "Auditorning kasbiy axloq kodeksi haqida aytib bering",
        "hr":        "Talil yoki kasallik varaqasini qanday rasmiylashtirish mumkin?",
        "career":    "Baker Tilly Tashkentda martaba zinapoyasi qanday?",
        "probation": "Sinov muddati qanday otadi? Mendan nima kutiladi?",
        "it":        "Qanday IT vositalar ishlatiladi? Kirish huquqlarini qanday olish mumkin?",
        "culture":   "Kompaniyaning korporativ madaniyati va qadriyatlari haqida aytib bering",
        "training":  "Oqitish, sertifikatsiya va kasbiy rivojlanish imkoniyatlari qanday?",
    },
}

GREETINGS = {
    "ru": (
        "👋 Добро пожаловать в Baker Tilly Tashkent!\n\n"
        "Я ваш персональный помощник по адаптации. "
        "Отвечу на любые вопросы о компании, процедурах и карьере.\n\n"
        "Выберите тему или напишите свой вопрос:"
    ),
    "uz": (
        "👋 Baker Tilly Tashkentga xush kelibsiz!\n\n"
        "Men sizning shaxsiy moslashuv yordamchisiman. "
        "Kompaniya, jarayonlar va martabangiz haqida savollarga javob beraman.\n\n"
        "Mavzuni tanlang yoki savolingizni yozing:"
    ),
}

SYSTEM_PROMPTS = {
    "ru": """Ты тёплый, профессиональный помощник по онбордингу в Baker Tilly Tashkent.
Отвечай ТОЛЬКО на русском языке. Используй простой понятный текст без markdown.

ТРУДОВОЙ РАСПОРЯДОК:
- Рабочие часы: 9:00-18:00, пн-пт, обед 13:00-14:00
- Дресс-код: деловой для клиентов; деловой повседневный в офисе (джинсы запрещены пн-вт)
- Удалёнка: гибрид после испытательного срока (до 2 дней/нед, с согласия руководителя)
- Опоздание: немедленно уведомить руководителя
- Медосмотр: оплачивается компанией

КОДЕКС ЭТИКИ:
- Независимость и объективность — обязательное требование
- Конфиденциальность данных клиентов — строгая
- Личная связь с клиентом — немедленно сообщить партнёру
- Подарки от клиентов свыше 50 000 UZS — запрещены
- Публикации о клиентах в соцсетях — только с согласования
- Ежегодное обучение по этике — обязательно

HR-ПРОЦЕДУРЫ:
- Отпуск: 21 рабочий день в год (пропорционально в первый год)
- Оформление отпуска: уведомить HR и руководителя за 2 недели, форма в 1С, подпись руководителя
- Больничный: медсправка + сдать в HR за 3 рабочих дня после выхода
- Зарплата: 10-го числа каждого месяца
- Аванс: до 25-го (макс 50%), письменный запрос в бухгалтерию
- Медстраховка: с 4-го месяца работы
- Корпоративный телефон: от уровня старший аудитор

КАРЬЕРНАЯ ЛЕСТНИЦА:
- Младший аудитор -> Аудитор -> Старший аудитор -> Менеджер -> Старший менеджер -> Партнёр
- Оценка: ежегодно, ноябрь-декабрь
- KPI: норма часов, качество работы, отзывы клиентов, профразвитие
- ACCA/CPA/DipIFR/CIA: 70% стоимости компенсируется (обязательство 1 год)

ИСПЫТАТЕЛЬНЫЙ СРОК:
- 3 месяца
- Неделя 1: ориентация с HR, наставник, KPI
- Неделя 6: промежуточная встреча с руководителем
- Месяц 3: официальная оценка
- Зарплата как в договоре

IT:
- День 1: email (имя.фамилия@bakertilly.uz), Teams, рабочее место
- Программы: Microsoft 365, Teams, CaseWare, IDEA/ACL, TimeBilling
- VPN обязателен для удалёнки
- IT-поддержка: it@bakertilly.uz

КОРПОРАТИВНАЯ КУЛЬТУРА:
- Открытые двери: любой сотрудник может обратиться к любому руководителю
- Понедельник 9:15 — командная встреча
- Последняя пятница месяца — общий сбор
- Baker Tilly International: стажировки за рубежом после 2+ лет
- Ценности: честность, качество, уважение, развитие, командная работа

ОБУЧЕНИЕ:
- Первые 2 недели: структурированный онбординг
- Ежемесячные тренинги (пятница 17:00)
- E-learning портал Baker Tilly: 500+ курсов
- CPE: 40 часов/год для лицензированных аудиторов
- Английский язык: 50% субсидирование

КОНТАКТЫ:
- HR: hr@bakertilly.uz
- IT: it@bakertilly.uz
- Общие: info@bakertilly.uz

Если не знаешь ответа — направь в HR: hr@bakertilly.uz""",

    "uz": """Sen Baker Tilly Tashkentda onboarding yordamchisisiz.
FAQAT o'zbek tilida (lotin) javob ber. Oddiy matn ishlat.

MEHNAT TARTIBI:
- Ish vaqti: 9:00-18:00, du-ju, tushlik 13:00-14:00
- Kiyim: mijozlar bilan rasmiy; ofisda ishchan-erkin (du-se jinsi taqiqlanadi)
- Masofaviy: sinov muddatidan keyin (haftada 2 kun, menejer roziligi)
- Kechikish: darhol menejerga xabar ber

AXLOQ KODEKSI:
- Mustaqillik va obyektivlik — majburiy
- Mijoz malumotlari — qatiy maxfiy
- 50 000 UZS dan ortiq sovga — taqiqlangan
- Yillik axloq oqitishi — majburiy

HR JARAYONLARI:
- Yillik talil: 21 ish kuni
- Talil: 2 hafta oldin xabar, 1C shakl, menejer imzosi
- Kasallik: tibbiy malumotnoma, 3 kun ichida HR ga
- Ish haqi: 10-sanada
- Tibbiy sugurta: 4-oydan

MARTABA ZINAPOYASI:
- Kichik auditor -> Auditor -> Katta auditor -> Menejer -> Katta menejer -> Hamkor
- Yillik baholash: noyabr-dekabr
- ACCA/CPA/DipIFR/CIA: 70% qoplanadi

SINOV MUDDATI:
- 3 oy
- 1-hafta: HR, ustoz, KPI
- 3-oy: rasmiy baholash

IT:
- 1-kun: email (ism.familiya@bakertilly.uz), Teams
- Dasturlar: Microsoft 365, CaseWare, TimeBilling
- IT yordam: it@bakertilly.uz

KONTAKTLAR:
- HR: hr@bakertilly.uz
- IT: it@bakertilly.uz

Javob bilmasang: hr@bakertilly.uz ga yubor""",
}

# ── Gemini via HTTP ────────────────────────────────────────────────────────────
def ask_gemini(lang: str, history: list, user_text: str) -> str:
    # Build conversation contents
    contents = []
    for m in history[-20:]:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_text}]})

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPTS[lang]}]
        },
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 800,
            "temperature": 0.7,
        }
    }

    resp = requests.post(GEMINI_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

# ── Keyboards ─────────────────────────────────────────────────────────────────
def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский",    callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
    ]])

def topics_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(TOPICS[lang]), 2):
        rows.append([
            InlineKeyboardButton(label, callback_data=f"topic_{tid}")
            for label, tid in TOPICS[lang][i:i+2]
        ])
    rows.append([InlineKeyboardButton(
        "🌐 Сменить язык / Tilni ozgartirish", callback_data="change_lang"
    )])
    return InlineKeyboardMarkup(rows)

# ── Handlers ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Добро пожаловать / Xush kelibsiz!\n\nВыберите язык / Tilni tanlang:",
        reply_markup=lang_keyboard(),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        context.user_data.update({"lang": lang, "history": []})
        await query.edit_message_text(GREETINGS[lang], reply_markup=topics_keyboard(lang))

    elif query.data == "change_lang":
        context.user_data.clear()
        await query.edit_message_text(
            "🌐 Выберите язык / Tilni tanlang:",
            reply_markup=lang_keyboard(),
        )

    elif query.data.startswith("topic_"):
        topic_id = query.data.split("_", 1)[1]
        lang = context.user_data.get("lang", "ru")
        await process_message(update, context, TOPIC_QUESTIONS[lang][topic_id], from_button=True)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "lang" not in context.user_data:
        await update.message.reply_text(
            "Пожалуйста, начните с /start\nIltimos, /start buyrug'ini yuboring",
            reply_markup=lang_keyboard(),
        )
        return
    await process_message(update, context, update.message.text)

async def process_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    text: str, from_button: bool = False,
) -> None:
    lang    = context.user_data.get("lang", "ru")
    history = context.user_data.setdefault("history", [])

    msg_obj = update.callback_query.message if from_button else update.message
    await context.bot.send_chat_action(msg_obj.chat_id, "typing")

    if from_button:
        await msg_obj.reply_text(text)

    try:
        reply = ask_gemini(lang, history, text)
        history.append({"role": "user",      "content": text})
        history.append({"role": "assistant", "content": reply})
        await msg_obj.reply_text(reply, reply_markup=topics_keyboard(lang))

    except Exception as e:
        err = str(e)
        print(f"[ERROR] {err}")
        # Hide URL from error to protect API key
        safe_err = err.split("?key=")[0] if "?key=" in err else err[:200]
        msgs = {
            "ru": f"Ошибка соединения: {safe_err}\n\nПопробуйте позже или: hr@bakertilly.uz",
            "uz": f"Ulanish xatosi: {safe_err}\n\nhr@bakertilly.uz ga yozing",
        }
        await msg_obj.reply_text(msgs[lang])

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Baker Tilly Onboarding Bot started.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
