# main.py
from fastapi import FastAPI, Request, HTTPException
import logging
import httpx
import os
import json

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ozan-webhook")

# Получение переменных из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Отправка уведомлений в Telegram
async def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не установлены")
        return
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                TELEGRAM_API_URL,
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке в Telegram: {e}")

# Вебхук-обработчик
@app.post("/webhook/ozan")
async def ozan_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("Ошибка при чтении JSON: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info("Webhook получен:\n" + json.dumps(payload, indent=2))

    transaction_type = payload.get("type", "").lower()
    status = payload.get("status")
    user_id = payload.get("user_id")
    amount = payload.get("amount")
    currency = payload.get("currency", "TRY")
    transaction_id = payload.get("transaction_id")

    if transaction_type == "deposit" and status == "SUCCESS":
        msg = f"💰 Пополнение от пользователя {user_id}\nСумма: {amount} {currency}\nТранзакция: {transaction_id}"
        await send_telegram_message(msg)

    elif transaction_type == "transaction" and status == "SUCCESS":
        msg = f"✅ Успешная транзакция от {user_id}\nСумма: {amount} {currency}\nТранзакция: {transaction_id}"
        await send_telegram_message(msg)

    else:
        logger.warning("Неизвестный тип транзакции или ошибка")
        await send_telegram_message("⚠️ Получен неизвестный или неуспешный вебхук")

    return {"status": "received"}
