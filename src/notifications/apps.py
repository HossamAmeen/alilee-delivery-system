import firebase_admin
from django.apps import AppConfig
from firebase_admin import credentials


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        import notifications.signals
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase_cred.json")
            firebase_admin.initialize_app(cred)
