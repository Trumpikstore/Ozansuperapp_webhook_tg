from flask import Flask, request, jsonify
import logging
import json
import requests

app = Flask(__name__)

# 🔐 Укажи здесь свои данные:
TELEGRAM_TOKEN = "7:7"   # ← замени на свой токен
TELEGRAM_CHAT_ID =               # ← замени на свой chat_id (без кавычек)

logging.basicConfig(
    filename="ozan_webhook.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def send_telegram_message(text: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("TELEGRAM_TOKEN или TELEGRAM_CHAT_ID не заданы")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        response = requests.post(url, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке в Telegram: {e}")
        return False

@app.route("/webhook/ozan", methods=["POST"])
def ozan_webhook():
    try:
        logging.info("=== Получен запрос ===")
        logging.info(f"Headers: {dict(request.headers)}")

        data = request.get_json(force=True, silent=True)
        if data is None:
            msg = "Тело запроса не содержит корректный JSON"
            logging.error(msg)
            return jsonify({"error": msg}), 400

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception as e:
                msg = f"Не удалось распарсить вложенный JSON: {e}"
                logging.error(msg)
                return jsonify({"error": msg}), 400

        if not isinstance(data, dict):
            msg = f"Ожидался JSON-объект (dict), но получен {type(data).__name__}"
            logging.error(msg)
            return jsonify({"error": msg}), 400

        required_fields = [
            "amount", "transactionType", "transactionStatus",
            "firstName", "lastName", "accountInfo", "transactionId"
        ]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            msg = f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
            logging.error(msg)
            return jsonify({"error": msg}), 400

        amount_info = data.get("amount", {})
        if not isinstance(amount_info, dict):
            msg = "'amount' должен быть объектом"
            logging.error(msg)
            return jsonify({"error": msg}), 400

        value = amount_info.get("value")
        currency = amount_info.get("currency")

        msg = (
            f"💳 Ozan событие:\n"
            f"Тип: {data.get('transactionType')}\n"
            f"Статус: {data.get('transactionStatus')}\n"
            f"Сумма: {value} {currency}\n"
            f"Клиент: {data.get('firstName')} {data.get('lastName')}\n"
            f"Счёт: {data.get('accountInfo')}\n"
            f"ID: {data.get('transactionId')}"
        )

        if not send_telegram_message(msg):
            logging.error("Не удалось отправить сообщение в Telegram")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.error(f"❌ Ошибка обработки запроса: {e}", exc_info=True)
        send_telegram_message(f"❌ Ошибка в webhook: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return "Ozan Webhook Listener активен", 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
