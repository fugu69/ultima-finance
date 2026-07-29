import requests
from celery import shared_task
from .models import OutboxEvent

# URL второго приложения (пока локальный)
FASTAPI_WEBHOOK_URL = "http://127.0.0.1:8000/api/transfer/webhook"

@shared_task
def process_outbox_events():
    events = OutboxEvent.objects.filter(status=OutboxEvent.StatusChoices.PENDING)[:50]

    for event in events:
        try:
            # Отправляем данные во второе приложение
            response = requests.post(
                FASTAPI_WEBHOOK_URL,
                json=event.payload,
                timeout=3
            )

            # Если FastAPI дал добро
            if response.status_code == 200:
                event.status = OutboxEvent.StatusChoices.SENT
                event.save(update_fields=["status", "updated_at"])

        except requests.RequestException:
            # Если FastAPI выключен, нет сети или таймаут — мы попадаем сюда.
            # Ничего не делаем (pass). Статус остается PENDING.
            # При следующем запуске функция снова возьмет эту запись и попробует отправить.
            pass