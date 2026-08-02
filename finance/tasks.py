import requests
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from .models import OutboxEvent

FASTAPI_WEBHOOK_URL = f"{settings.FASTAPI_BASE_URL}/api/transfer/webhook/"

# ⚡ ТАСКА 1: Мгновенная отправка ОДНОГО события по ID
@shared_task
def send_single_outbox_event(event_id: int):
    try:
        event = OutboxEvent.objects.get(id=event_id, status=OutboxEvent.StatusChoices.PENDING)
    except OutboxEvent.DoesNotExist:
        return  # Событие уже отправлено или его нет

    data_to_send = event.payload.copy()
    data_to_send["event_id"] = event.id

    try:
        response = requests.post(FASTAPI_WEBHOOK_URL, json=data_to_send, timeout=3)
        if response.status_code == 200:
            event.status = OutboxEvent.StatusChoices.SENT
            event.save(update_fields=["status", "updated_at"])
        else:
            print(f"❌ FastAPI не принял данные! Код: {response.status_code}, Ответ: {response.text}")
    except requests.RequestException as e:
        print(f"❌ Ошибка сети при отправке в FastAPI: {e}")


# 🔄 ТАСКА 2: Периодический фоновый подбор застрявших событий (Fallback)
@shared_task
def process_outbox_events():
    events = OutboxEvent.objects.filter(status=OutboxEvent.StatusChoices.PENDING)[:50]

    for event in events:
        send_single_outbox_event(event.id)


@shared_task
def cleanup_processed_outbox_events(days_to_keep=30):
    """
    Удаляет события со статусом SENT, созданные более 30 дней назад.
    """
    cutoff = timezone.now() - timedelta(days=days_to_keep)

    # Фильтруем по полю status и значению StatusChoices.SENT
    deleted_count, _ = OutboxEvent.objects.filter(
        status=OutboxEvent.StatusChoices.SENT, created_at__lt=cutoff
    ).delete()

    return f"Удалено {deleted_count} старых Outbox-записей."
