# -*- coding: utf-8 -*-
"""
Telegram-бот: тест «5 точек утечки денег у селлера на маркетплейсах»
Чурюмова Консалтинг

Запуск:  python bot.py
Перед запуском впишите свой токен в переменную BOT_TOKEN ниже.
Библиотека: python-telegram-bot версии 21 и выше
   установка:  pip install "python-telegram-bot>=21"
"""

import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

# ============================================================
# НАСТРОЙКИ — здесь меняете под себя
# ============================================================

# 1) Токен бота. Получите у @BotFather.
#    Бот возьмёт токен из переменной окружения BOT_TOKEN (нужно для хостинга).
#    Если её нет (например, при запуске на своём компьютере) — возьмёт строку ниже.
BOT_TOKEN = os.getenv("BOT_TOKEN") or "СЮДА_ВСТАВЬТЕ_ТОКЕН"

# 2) Куда вести кнопку «Написать менеджеру». Ваш username без @ -> ссылка t.me
MANAGER_USERNAME = "ChurCons"           # t.me/ChurCons
MANAGER_PHONE = "+7 937 768 7212"
SITE = "chur-buh.ru"

# 3) (необязательно) ID чата/группы, куда бот пришлёт заявку с контактом клиента.
#    Если не нужно — оставьте None. Как узнать ID — см. инструкцию.
LEADS_CHAT_ID = None   # например: -1001234567890

# ============================================================
# Логи (чтобы видеть ошибки в консоли)
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ============================================================
# СОДЕРЖАНИЕ ТЕСТА
# Каждый вопрос: текст + список ответов (подпись, баллы)
# ============================================================

QUESTIONS = [
    {
        "key": "q1",
        "title": "Точка №1 из 5: Сверка с отчётом маркетплейса",
        "text": (
            "Главная утечка №1: учёт не сверяют с отчётом о реализации площадки. "
            "Селлер видит поступление на счёт и считает его выручкой, а реальные "
            "продажи, комиссии и удержания — другие.\n\n"
            "<b>Что сделать (2 минуты):</b>\n"
            "Откройте «Отчёт о реализации» (отчёт комиссионера) в кабинете WB или Ozon "
            "за последний месяц. Сравните сумму продаж в отчёте с выручкой в вашем учёте.\n\n"
            "<b>❓ Совпадает ли выручка в учёте с отчётом маркетплейса?</b>"
        ),
        "answers": [
            ("✅ Да, сверяю каждый месяц по отчёту", 3),
            ("⚠️ Примерно сходится, детально не сверяю", 1),
            ("❌ Считаю по тому, что пришло на счёт", 0),
            ("❓ Не знаю, как это сверяется", 0),
        ],
    },
    {
        "key": "q2",
        "title": "Точка №2 из 5: Учёт всех удержаний площадки",
        "text": (
            "Маркетплейс удерживает не только комиссию: логистика, хранение, обратная "
            "логистика, штрафы, платная приёмка, реклама. Если эти расходы не в учёте — "
            "вы не видите реальную прибыль и можете переплачивать налог.\n\n"
            "<b>Что сделать:</b>\n"
            "Возьмите детализацию удержаний из отчёта площадки за месяц. Проверьте, все ли "
            "статьи отражены в ваших расходах.\n\n"
            "<b>❓ Все удержания площадки попадают в учёт?</b>"
        ),
        "answers": [
            ("✅ Да, все статьи разнесены по расходам", 3),
            ("⚠️ Часть учитываю, часть теряется", 1),
            ("❌ Учитываю только комиссию", 0),
            ("❓ Не знаю", 0),
        ],
    },
    {
        "key": "q3",
        "title": "Точка №3 из 5: Налоговый режим и ставка",
        "text": (
            "Частая переплата: селлер на УСН «Доходы» 6% платит со всей выручки, хотя для "
            "торговли на маркетплейсах часто выгоднее «Доходы минус расходы». А ещё есть "
            "регионы со ставкой УСН 1% — на этом теряют сотни тысяч в год.\n\n"
            "<b>Что сделать:</b>\n"
            "Посмотрите свой режим и ставку. Прикиньте долю расходов (комиссии + закупка + "
            "логистика). Если расходы выше 60% — на «Доходы 6%» вы, скорее всего, переплачиваете.\n\n"
            "<b>❓ Уверены, что у вас оптимальная ставка налога?</b>"
        ),
        "answers": [
            ("✅ Да, режим подбирали под мои расходы", 3),
            ("⚠️ Плачу как есть, давно не пересчитывал", 1),
            ("❌ Плачу 6% со всей выручки, расходы большие", 0),
            ("❓ Не знаю свою ставку", 0),
        ],
    },
    {
        "key": "q4",
        "title": "Точка №4 из 5: Совпадение с тем, что видит ФНС",
        "text": (
            "Бухгалтер говорит «всё хорошо», а на ЕНС копится долг и пени. Маркетплейсы "
            "передают данные о ваших оборотах — ФНС видит расхождения.\n\n"
            "<b>Что сделать:</b>\n"
            "1. Зайдите в личный кабинет на nalog.ru\n"
            "2. Посмотрите состояние ЕНС (Единого налогового счёта)\n"
            "3. Проверьте, нет ли долга и неотвеченных требований\n\n"
            "<b>❓ Какой баланс на ЕНС и есть ли требования?</b>"
        ),
        "answers": [
            ("✅ Сальдо ноль или плюс, требований нет", 3),
            ("⚠️ Бывают мелкие долги / пени", 1),
            ("❌ Долг или висят требования", 0),
            ("❓ Нет доступа / не знаю", 0),
        ],
    },
    {
        "key": "q5",
        "title": "Точка №5 из 5: Порядок в первичке и возвратах",
        "text": (
            "У селлеров огромный поток операций: продажи, возвраты, корректировки. Если "
            "первичка ведётся «тяп-ляп», часть расходов теряется (переплата налога), а "
            "возвраты задваиваются.\n\n"
            "<b>Что сделать:</b>\n"
            "Попросите оборотно-сальдовую ведомость (ОСВ) за прошлый квартал. Посмотрите "
            "остатки по счетам расчётов и товаров. Красные (отрицательные) остатки — плохой знак.\n\n"
            "<b>❓ Есть ли в учёте отрицательные / зависшие остатки?</b>"
        ),
        "answers": [
            ("✅ Нет, всё чисто", 3),
            ("⚠️ Пара мелких вопросов есть", 1),
            ("❌ Много минусов / бардак в возвратах", 0),
            ("❓ Не знаю / не просил ОСВ", 0),
        ],
    },
]

MAX_SCORE = sum(max(p for _, p in q["answers"]) for q in QUESTIONS)  # = 15


# ============================================================
# ТЕКСТЫ ЭКРАНОВ
# ============================================================

WELCOME = (
    "Чурюмова Консалтинг — бухгалтерия и налоги для селлеров маркетплейсов.\n\n"
    "Мы ведём учёт продавцов на Wildberries, Ozon и Яндекс.Маркете так, чтобы вы не "
    "теряли деньги на скрытых удержаниях, штрафах и переплате налогов.\n\n"
    "<b>Мы помогаем:</b>\n"
    "— Видеть реальную прибыль, а не «грязную» выручку\n"
    "— Считать налог только с того, что осталось у вас\n"
    "— Законно снижать налог (ставка УСН 1% в Калмыкии)\n"
    "— Спокойно проходить требования и проверки ФНС\n\n"
    "Выберите удобный способ связи:"
)

INTRO = (
    "Вы открыли экспресс-инструмент от Чурюмовой Консалтинг — мы 19 лет в бухгалтерии "
    "и специализируемся только на маркетплейсах.\n\n"
    "<b>Проблема:</b> большинство селлеров считают выручкой сумму, пришедшую от площадки. "
    "Но маркетплейс уже удержал комиссию, логистику, хранение, штрафы и рекламу. А налог "
    "часто считают со всей суммы поступлений — и продавец переплачивает.\n\n"
    "<b>Наша цель:</b> не грузить вас проводками. Дадим 5 простых точек, где у селлера "
    "утекают деньги. Вы сами проверите учёт — даже если не разбираетесь в цифрах.\n\n"
    "Пройти проверку — 5 минут.\n\n👇 Что делаем?"
)


def result_text(score: int) -> str:
    if score >= 12:
        return (
            f"Спасибо! Вы прошли проверку по 5 точкам.\n\n"
            f"<b>Ваш результат: {score} из {MAX_SCORE} баллов.</b>\n\n"
            "🟢 <b>Зелёная зона.</b> Ваш учёт под контролем — вы один из немногих "
            "селлеров, кто реально видит свои деньги и налоги.\n\n"
            "Но даже здесь есть что докрутить: комиссии площадок меняются, а ставку "
            "налога можно снизить законно — например, до 1% через регистрацию в Калмыкии. "
            "На консультации покажем, где ещё можно сэкономить."
        )
    elif score >= 6:
        return (
            f"Спасибо! Вы прошли проверку по 5 точкам.\n\n"
            f"<b>Ваш результат: {score} из {MAX_SCORE} баллов.</b>\n\n"
            "🟡 <b>Жёлтая зона.</b> Есть зоны риска. Скорее всего, вы теряете деньги на "
            "скрытых удержаниях или переплачиваете налог — просто пока этого не видно.\n\n"
            "Вы правильно сделали, что проверили. Расхождения с отчётами площадок и "
            "«красные» остатки часто приводят к тому, что ФНС доначисляет налоги, которые "
            "вы уже фактически отдали площадке.\n\n"
            "Мы можем провести экспресс-аудит и за 15 минут показать на цифрах, где у вас "
            "«дыра» и сколько она уже стоила."
        )
    else:
        return (
            f"Спасибо! Вы прошли проверку по 5 точкам.\n\n"
            f"<b>Ваш результат: {score} из {MAX_SCORE} баллов.</b>\n\n"
            "🔴 <b>Красная зона.</b> Высокий риск. Похоже, учёт не сверяется с "
            "маркетплейсами, а налог считается «вслепую». Вы почти наверняка переплачиваете "
            "налог и рискуете доначислениями от ФНС.\n\n"
            "Это лечится, и чем раньше — тем дешевле. На консультации разберём вашу "
            "ситуацию и составим план первых шагов."
        )


FINAL_OFFER = (
    "<b>На консультации с экспертом Чурюмовой Консалтинг вы получите:</b>\n"
    "1. Разбор вашей ситуации по результатам теста.\n"
    "2. Расчёт, сколько вы реально теряете на удержаниях и налоге.\n"
    "3. План первых 3 шагов, чтобы закрыть утечки.\n\n"
    "Что делать дальше?"
)


# ============================================================
# КЛАВИАТУРЫ
# ============================================================

def kb_welcome():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Пройти тест «5 точек утечки денег»", callback_data="test_intro")],
        [InlineKeyboardButton("💬 Получить консультацию", callback_data="consult_start")],
        [InlineKeyboardButton("📲 Написать менеджеру в Telegram", url=f"https://t.me/{MANAGER_USERNAME}")],
    ])


def kb_intro():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Начать проверку", callback_data="ask_name_for_test")],
        [InlineKeyboardButton("📞 Срочный вопрос к эксперту", url=f"https://t.me/{MANAGER_USERNAME}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_welcome")],
    ])


def kb_question(q_index: int):
    q = QUESTIONS[q_index]
    rows = []
    for a_index, (label, _points) in enumerate(q["answers"]):
        rows.append([InlineKeyboardButton(label, callback_data=f"ans_{q_index}_{a_index}")])
    return InlineKeyboardMarkup(rows)


def kb_final():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Написать в Telegram (быстрый ответ)", url=f"https://t.me/{MANAGER_USERNAME}")],
        [InlineKeyboardButton("📞 Заказать звонок", callback_data="consult_start")],
        [InlineKeyboardButton("🔁 Пройти тест заново", callback_data="ask_name_for_test")],
    ])


def kb_phone():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Отправить мой номер", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )


# ============================================================
# ЛОГИКА
#
# context.user_data["stage"] — на каком шаге диалога человек:
#   "test_name"     — ждём имя (перед тестом)
#   "test_phone"    — ждём телефон (перед тестом)
#   "consult_name"  — ждём имя/компанию (консультация)
#   "consult_topic" — ждём описание запроса (консультация)
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    name = update.effective_user.first_name or ""
    await update.message.reply_text(
        f"Здравствуйте, {name}!\n\n{WELCOME}",
        reply_markup=kb_welcome(),
        parse_mode="HTML",
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- Стартовое меню: Назад ---
    if data == "back_welcome":
        await query.message.reply_text(WELCOME, reply_markup=kb_welcome(), parse_mode="HTML")

    # --- Ветка ТЕСТ: вступление ---
    elif data == "test_intro":
        await query.message.reply_text(INTRO, reply_markup=kb_intro(), parse_mode="HTML")

    # --- Ветка ТЕСТ: перед тестом спрашиваем имя ---
    elif data == "ask_name_for_test":
        context.user_data["stage"] = "test_name"
        context.user_data["score"] = 0
        await query.message.reply_text(
            "Перед началом — пара секунд на знакомство.\n\nНапишите ваше имя:",
            reply_markup=ReplyKeyboardRemove(),
        )

    # --- Ответы на вопросы теста ---
    elif data.startswith("ans_"):
        _, q_idx, a_idx = data.split("_")
        q_idx, a_idx = int(q_idx), int(a_idx)
        points = QUESTIONS[q_idx]["answers"][a_idx][1]
        context.user_data["score"] = context.user_data.get("score", 0) + points

        next_idx = q_idx + 1
        if next_idx < len(QUESTIONS):
            await send_question(query.message, context, next_idx)
        else:
            await finish_test(query.message, context)

    # --- Ветка КОНСУЛЬТАЦИЯ: спрашиваем имя/компанию ---
    elif data == "consult_start":
        context.user_data["stage"] = "consult_name"
        await query.message.reply_text(
            "Напишите ваше имя или название компании:",
            reply_markup=ReplyKeyboardRemove(),
        )


async def send_question(message, context, q_index: int):
    q = QUESTIONS[q_index]
    await message.reply_text(
        f"<b>{q['title']}</b>\n\n{q['text']}",
        reply_markup=kb_question(q_index),
        parse_mode="HTML",
    )


async def finish_test(message, context):
    score = context.user_data.get("score", 0)
    await message.reply_text(result_text(score), parse_mode="HTML")
    await message.reply_text(FINAL_OFFER, reply_markup=kb_final(), parse_mode="HTML")
    # заявка с результатом (имя/телефон собрали до теста)
    await send_lead_to_owner(
        context,
        name=context.user_data.get("lead_name", "—"),
        phone=context.user_data.get("lead_phone", "—"),
        kind="Тест",
        extra=f"Результат: {score} из {MAX_SCORE}",
        username=context.user_data.get("lead_username", "—"),
    )


# ============================================================
# ОБРАБОТКА ТЕКСТА И КОНТАКТА (зависит от stage)
# ============================================================

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Человек нажал кнопку «Отправить мой номер»."""
    if context.user_data.get("stage") == "test_phone":
        phone = update.message.contact.phone_number
        await save_phone_and_start_test(update, context, phone)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик текста. Реагирует по текущему шагу диалога."""
    stage = context.user_data.get("stage")
    text = update.message.text.strip()
    user = update.effective_user
    context.user_data["lead_username"] = f"@{user.username}" if user.username else "—"

    # ----- Тест: получили имя -> спрашиваем телефон -----
    if stage == "test_name":
        context.user_data["lead_name"] = text
        context.user_data["stage"] = "test_phone"
        await update.message.reply_text(
            f"Приятно познакомиться, {text}!\n\n"
            "Оставьте номер телефона — пришлём результат и свяжемся, если будут вопросы.\n"
            "Нажмите кнопку ниже или впишите номер вручную в формате +79XXXXXXXXX",
            reply_markup=kb_phone(),
        )

    # ----- Тест: получили телефон текстом -> запускаем тест -----
    elif stage == "test_phone":
        await save_phone_and_start_test(update, context, text)

    # ----- Консультация: получили имя/компанию -> спрашиваем запрос -----
    elif stage == "consult_name":
        context.user_data["lead_name"] = text
        context.user_data["stage"] = "consult_topic"
        await update.message.reply_text("Кратко опишите: «С чем нужна помощь?»")

    # ----- Консультация: получили запрос -> финал -----
    elif stage == "consult_topic":
        topic = text
        context.user_data["stage"] = None
        await update.message.reply_text(
            "Спасибо!\nМы получили ваш запрос и скоро свяжемся с вами.\n\n"
            f"Если удобнее — пишите сразу: @{MANAGER_USERNAME} или {MANAGER_PHONE}.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await send_lead_to_owner(
            context,
            name=context.user_data.get("lead_name", "—"),
            phone="(не указан)",
            kind="Консультация",
            extra=f"Запрос: {topic}",
            username=context.user_data.get("lead_username", "—"),
        )


async def save_phone_and_start_test(update, context, phone):
    """Сохраняем телефон и запускаем первый вопрос теста."""
    context.user_data["lead_phone"] = phone
    context.user_data["stage"] = None
    context.user_data["score"] = 0
    await update.message.reply_text(
        "Отлично, начинаем проверку! 👇",
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_question(update.message, context, 0)


# ============================================================
# ОТПРАВКА ЗАЯВКИ ВЛАДЕЛЬЦУ
# ============================================================

async def send_lead_to_owner(context, name, phone, kind, extra, username):
    if not LEADS_CHAT_ID:
        return
    lead = (
        f"🔔 <b>Новая заявка из бота</b>\n"
        f"Тип: {kind}\n"
        f"Имя/компания: {name}\n"
        f"Телефон: {phone}\n"
        f"Username: {username}\n"
        f"{extra}"
    )
    try:
        await context.bot.send_message(LEADS_CHAT_ID, lead, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Не удалось отправить заявку: {e}")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return


def start_http_server():
    port = int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"✅ HTTP server listening on port {port}")
    server.serve_forever()


# ============================================================
# ЗАПУСК
# ============================================================

def main():
    if not BOT_TOKEN or BOT_TOKEN == "СЮДА_ВСТАВЬТЕ_ТОКЕН":
        raise SystemExit(
            "❌ Токен не задан. Либо впишите его в строку BOT_TOKEN в коде, "
            "либо задайте переменную окружения BOT_TOKEN на хостинге."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    thread = threading.Thread(target=start_http_server, daemon=True)
    thread.start()

    print("✅ Бот запущен. Откройте его в Telegram и нажмите /start")
    app.run_polling()


if __name__ == "__main__":
    main()
