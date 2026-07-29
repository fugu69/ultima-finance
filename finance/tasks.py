import requests
from celery import shared_task
from .models import OutboxEvent

# 1. ДОБАВИЛИ СЛЭШ В КОНЕЦ URL
FASTAPI_WEBHOOK_URL = "http://127.0.0.1:8000/api/transfer/webhook/"


@shared_task
def process_outbox_events():
    events = OutboxEvent.objects.filter(status=OutboxEvent.StatusChoices.PENDING)[:50]

    for event in events:
        try:
            # 2. ДОБАВЛЯЕМ event_id НА ЛЕТУ ПЕРЕД ОТПРАВКОЙ (если ты этого еще не сделал)
            data_to_send = event.payload.copy()
            data_to_send["event_id"] = event.id

            response = requests.post(FASTAPI_WEBHOOK_URL, json=data_to_send, timeout=3)

            if response.status_code == 200:
                event.status = OutboxEvent.StatusChoices.SENT
                event.save(update_fields=["status", "updated_at"])
            else:
                # 3. ВЫВОДИМ ОШИБКУ В ТЕРМИНАЛ CELERY
                print(
                    f"❌ FastAPI не принял данные! Код: {response.status_code}, Ответ: {response.text}"
                )

        except requests.RequestException:
            pass
