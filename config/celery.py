import os
from celery import Celery

# 1. Указываем, где лежат настройки Джанго (папка config)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 2. Создаем сам экземпляр движка
app = Celery("config")

# 3. Говорим движку брать настройки из settings.py 
# (он найдет наш CELERY_BROKER_URL)
app.config_from_object("django.conf:settings", namespace="CELERY")

# 4. Просим Celery автоматически искать файлы tasks.py в твоих приложениях
app.autodiscover_tasks()