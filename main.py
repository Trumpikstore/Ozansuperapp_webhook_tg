from fastapi import FastAPI, Request, HTTPException
import logging
import httpx
import os
import json

app = FastAPI()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ozan-webhook")

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Приветствие — чтобы не было 404 на "/"
@app.get("/")
async def root():
    return {"status": "✅ Ozan webhook server is running"}

# Функция отправки Telegram-сообщения
async def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не установлены")
        return
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке в Telegram: {e}")

# Вебхук Ozan
@app.post("/webhook/ozan")
async def ozan_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("Ошибка при чтении JSON: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info("✅ Вебхук получен:\n" + json.dumps(payload, indent=2))

    # Распарси нужные поля
    transaction_type = payload.get("type", "").lower()
    status = payload.get("status")
    user_id = payload.get("user_id", "неизвестно")
    amount = payload.get("amount", "—")
    currency = payload.get("currency", "TRY")
    transaction_id = payload.get("transaction_id", "N/A")

    # Составим сообщение
    if transaction_type == "deposit" and status == "SUCCESS":
        msg = (
            f"💰 Пополнение от пользователя {user_id}\n"
            f"Сумма: {amount} {currency}\n"
            f"Транзакция: {transaction_id}"
        )
    elif transaction_type == "transaction" and status == "SUCCESS":
        msg = (
            f"✅ Успешная транзакция от {user_id}\n"
            f"Сумма: {amount} {currency}\n"
            f"Транзакция: {transaction_id}"
        )
    else:
        msg = f"⚠️ Получен webhook: неизвестный или неуспешный статус\n{json.dumps(payload, indent=2)}"

    await send_telegram_message(msg)
    return {"status": "received"}
