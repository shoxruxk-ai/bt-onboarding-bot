"""
Baker Tilly Tashkent — Onboarding Bot
Telegram bot powered by Google Gemini 1.5 Flash (free tier)
"""

import os
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ── Config ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)

# ── Content ──────────────────────────────────────────────────────────────────
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
        "hr":        "Ta'til yoki kasallik varaqasini qanday rasmiylashtirish mumkin?",
        "career":    "Baker Tilly Tashkentda martaba zinapoyasi qanday?",
        "probation": "Sinov muddati qanday o'tadi? Mendan nima kutiladi?",
        "it":        "Qanday IT vositalar ishlatiladi? Kirish huquqlarini qanday olish mumkin?",
        "culture":   "Kompaniyaning korporativ madaniyati va qadriyatlari haqida aytib bering",
        "training":  "O'qitish, sertifikatsiya va kasbiy rivojlanish imkoniyatlari qanday?",
    },
}

GREETINGS = {
    "ru": (
        "👋 Добро пожаловать в *Baker Tilly Tashkent*!\n\n"
        "Я ваш персональный помощник по адаптации. "
        "Отвечу на любые вопросы о компании, процедурах и карьере.\n\n"
        "Выберите тему или напишите свой вопрос:"
    ),
    "uz": (
        "👋 *Baker Tilly Tashkent*ga xush kelibsiz!\n\n"
        "Men sizning shaxsiy moslashuv yordamchisiman. "
        "Kompaniya, jarayonlar va martabangiz haqida savollarga javob beraman.\n\n"
        "Mavzuni tanlang yoki savolingizni yozing:"
    ),
}

SYSTEM_PROMPTS = {
    "ru": """Ты тёплый, профессиональный помощник по онбордингу в Baker Tilly Tashkent — международной аудиторской компании, входящей в глобальную сеть Baker Tilly.

Отвечай ТОЛЬКО на русском языке. Форматируй ответы для Telegram (*жирный*, _курсив_, • для списков).
Будь тёплым и практичным. Новые сотрудники волнуются — помоги им чувствовать себя комфортно.

ПРАВИЛА ВНУТРЕННЕГО ТРУДОВОГО РАСПОРЯДКА:
• Рабочие часы: 9:00–18:00, пн–пт, обед 13:00–14:00
• Дресс-код: деловой для встреч с клиентами; деловой повседневный в офисе (джинсы запрещены пн–вт)
• Удалённая работа: гибрид после испытательного срока (до 2 дней/нед, с согласия руководителя)
• Опоздание/отсутствие: немедленно уведомить руководителя
• Ежегодный медосмотр оплачивается компанией

КОДЕКС ПРОФЕССИОНАЛЬНОЙ ЭТИКИ:
• Независимость и объективность в аудите — абсолютное требование
• Строгая конфиденциальность данных клиентов
• Личная связь с клиентом — немедленно сообщить партнёру
• Нулевая терпимость к подаркам >50 000 UZS от клиентов
• Соцсети: запрещено публиковать о клиентах без согласования
• Соответствие стандартам IFAC и местной Палаты аудиторов
• Ежегодное обучение по этике — обязательно для всех

HR-ПРОЦЕДУРЫ:
• Ежегодный отпуск: 21 рабочий день (пропорционально в первый год)
• Оформление отпуска: уведомить HR и руководителя за 2 недели, заполнить форму в 1С, получить подпись руководителя
• Больничный: медсправка + сдать в HR в течение 3 рабочих дней после выхода
• Зарплата: 10-го числа каждого месяца
• Аванс: до 25-го предыдущего месяца (макс 50%), письменный запрос в бухгалтерию
• Медстраховка: активируется через 3 месяца
• Корпоративная связь: от уровня старший аудитор и выше

КАРЬЕРНАЯ ЛЕСТНИЦА:
• Младший аудитор → Аудитор → Старший аудитор → Менеджер → Старший менеджер → Партнёр
• Ежегодная оценка: ноябрь–декабрь
• KPI: выполнение нормы часов, качество работы, обратная связь клиентов, профразвитие
• Сертификации (ACCA, CPA, DipIFR, CIA): 70% стоимости компенсируется, обязательство остаться на 1 год

ИСПЫТАТЕЛЬНЫЙ СРОК:
• Длительность: 3 месяца
• Неделя 1: ориентация с HR, назначение наставника, постановка KPI
• Неделя 6: промежуточная встреча с руководителем
• Месяц 3: официальная оценка
• Зарплата в период испытания — как в договоре

IT И ИНСТРУМЕНТЫ:
• День 1: IT настраивает рабочее место и email (имя.фамилия@bakertilly.uz)
• Инструменты: Microsoft 365, Teams, SharePoint, Outlook
• Аудит: CaseWare Working Papers, IDEA/ACL для аналитики
• Учёт времени: ежедневно в TimeBilling (обязательно)
• VPN обязателен для удалённой работы
• IT-поддержка: it@bakertilly.uz или канал "IT Support" в Teams

КОРПОРАТИВНАЯ КУЛЬТУРА:
• Политика открытых дверей — любой сотрудник может обратиться к любому руководителю
• Еженедельные командные встречи: понедельник 9:15
• Ежемесячный общий сбор: последняя пятница месяца
• Baker Tilly International: глобальный портал знаний, стажировки за рубежом после 2+ лет
• Ценности: честность, качество, уважение, развитие, сотрудничество

ОБУЧЕНИЕ И РАЗВИТИЕ:
• Онбординг: первые 2 недели — структурированная программа
• Внутренние тренинги: каждый месяц (пятница 17:00)
• E-learning портал Baker Tilly: 500+ курсов бесплатно
• CPE: минимум 40 часов/год для лицензированных аудиторов
• Курсы английского: 50% субсидирование

КОНТАКТЫ:
• HR: shkabilov@bakertilly.uz
• IT: it@bakertilly.uz
• Общие вопросы: shkabilov@bakertilly.uz

Если не знаешь точного ответа — скажи обратиться в HR: shkabilov@bakertilly.uz""",

    "uz": """Siz Baker Tilly Tashkent — Baker Tilly xalqaro tarmog'iga kiruvchi audit va konsalting kompaniyasida onboarding yordamchisisiz.

FAQAT o'zbek tilida (lotin yozuvi) javob bering. Telegram formatlashdan foydalaning (*qalin*, _kursiv_, • ro'yxatlar uchun).
Iliq va amaliy bo'ling. Yangi xodimlar xavotirda — ularni qulay his qildiring.

ICHKI MEHNAT TARTIBI:
• Ish vaqti: 9:00–18:00, du–ju, tushlik 13:00–14:00
• Kiyim: mijozlar bilan rasmiy; ofisda ishchan-erkin (du–se jinsi taqiqlanadi)
• Masofaviy ish: sinov muddatidan keyin gibrid (haftada 2 kungacha, menejer roziligi)
• Kechikish/yo'qlik: darhol menejerga xabar bering
• Yillik tibbiy ko'rik kompaniya hisobidan

KASBIY AXLOQ KODEKSI:
• Mustaqillik va obyektivlik — auditing da mutlaq talab
• Mijoz ma'lumotlarining qat'iy maxfiyligi
• Mijoz bilan shaxsiy aloqa — darhol hamkorga xabar bering
• Mijozlardan >50 000 UZS sovg'aga nol bag'rikenglik
• Ijtimoiy tarmoqlarda mijozlar haqida kelishuvsiz e'lon taqiqlanadi
• Yillik axloq o'qitishi barcha uchun majburiy

HR JARAYONLARI:
• Yillik ta'til: 21 ish kuni (birinchi yili proporsional)
• Ta'til: HR va menejerga 2 hafta oldin xabar, 1C shaklini to'ldirish, menejer imzosi
• Kasallik: tibbiy ma'lumotnoma + ishga chiqqandan 3 kun ichida HR ga topshirish
• Ish haqi: har oyning 10-sanasida
• Avans: oldingi oyning 25-sanasigacha (maks 50%), buxgalteriyaga yozma ariza
• Tibbiy sug'urta: 3 oydan keyin faollashadi

MARTABA ZINAPOYASI:
• Kichik auditor → Auditor → Katta auditor → Menejer → Katta menejer → Hamkor
• Yillik baholash: noyabr–dekabr
• KPI: soat normasi, ish sifati, mijoz sharhi, kasbiy rivojlanish
• Sertifikatlar (ACCA, CPA, DipIFR, CIA): 70% qoplanadi, 1 yil qolish majburiyati

SINOV MUDDATI:
• Davomiyligi: 3 oy
• 1-hafta: HR bilan yo'naltirish, ustoz tayinlash, KPI belgilash
• 6-hafta: menejer bilan oraliq suhbat
• 3-oy: rasmiy baholash
• Sinov davrida ish haqi shartnomadagidek

IT VA VOSITALAR:
• 1-kun: IT email (ism.familiya@bakertilly.uz) va Teams kirishini sozlaydi
• Asosiy vositalar: Microsoft 365, Teams, SharePoint, Outlook
• Audit: CaseWare Working Papers, IDEA/ACL
• Vaqt hisobi: TimeBilling da har kuni majburiy
• Masofaviy ish uchun VPN majburiy
• IT yordam: it@bakertilly.uz yoki Teams "IT Support"

KORPORATIV MADANIYAT:
• Ochiq eshik siyosati — har qanday xodim har qanday rahbar bilan gaplasha oladi
• Haftalik yig'ilish: dushanba 9:15
• Oylik umumiy yig'ilish: oxirgi juma
• Baker Tilly International: global bilim portali, 2+ yildan keyin xalqaro stajirovka

O'QITISH VA RIVOJLANISH:
• Onboarding: dastlabki 2 hafta strukturali dastur
• Ichki treninglar: har oy (juma 17:00)
• E-learning portali: 500+ kurs bepul
• CPE: litsenziyali auditorlar uchun yiliga min 40 soat
• Ingliz tili: 50% subsidiya

KONTAKTLAR:
• HR: shkabilov@bakertilly.uz
• IT: it@bakertilly.uz

Aniq javob bilmasangiz: HR ga murojaat qilishni tavsiya eting: shkabilov@bakertilly.uz""",
}

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
        "🌐 Сменить язык / Tilni o'zgartirish", callback_data="change_lang"
    )])
    return InlineKeyboardMarkup(rows)

# ── Gemini call ───────────────────────────────────────────────────────────────
def ask_gemini(lang: str, history: list, user_text: str) -> str:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPTS[lang],
    )
    gemini_history = [
        {"role": "model" if m["role"] == "assistant" else "user",
         "parts": [m["content"]]}
        for m in history
    ]
    chat = model.start_chat(history=gemini_history)
    return chat.send_message(user_text).text

# ── Handlers ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "👋 *Добро пожаловать / Xush kelibsiz!*\n\nВыберите язык / Tilni tanlang:",
        parse_mode="Markdown",
        reply_markup=lang_keyboard(),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        context.user_data.update({"lang": lang, "history": []})
        await query.edit_message_text(
            GREETINGS[lang], parse_mode="Markdown",
            reply_markup=topics_keyboard(lang),
        )
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
    if len(history) > 20:
        history[:] = history[-20:]

    msg_obj = update.callback_query.message if from_button else update.message
    await context.bot.send_chat_action(msg_obj.chat_id, "typing")

    if from_button:
        await msg_obj.reply_text(f"_{text}_", parse_mode="Markdown")

    try:
        reply = ask_gemini(lang, history, text)
        history.append({"role": "user",      "content": text})
        history.append({"role": "assistant", "content": reply})
        await msg_obj.reply_text(reply, parse_mode="Markdown", reply_markup=topics_keyboard(lang))
    except Exception as e:
        errors = {
            "ru": "⚠️ Произошла ошибка. Попробуйте ещё раз или напишите на hr@bakertilly.uz",
            "uz": "⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring yoki hr@bakertilly.uz ga yozing",
        }
        await msg_obj.reply_text(errors[lang])
        print(f"Error: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("✅ Baker Tilly Onboarding Bot (Gemini) is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
