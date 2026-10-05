# ============================================================
# firebase_admin_setup.py
# Initialises the Firebase Admin SDK for server-side access to
# Auth (token checks), Firestore (database) and Cloud Storage.
# Initialisation happens on first use, so importing the app
# (e.g. in tests) does not need credentials.
# ============================================================

# ---- Imports ----
import firebase_admin
from firebase_admin import credentials, firestore, storage

from settings import get_settings


# ---- Firebase Initialisation ----
def get_firebase_app():
    if not firebase_admin._apps:
        settings = get_settings()
        if settings.firebase_credentials:
            cred = credentials.Certificate(settings.firebase_credentials)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"storageBucket": settings.storage_bucket})
    return firebase_admin.get_app()


# ---- Firestore and Storage Clients ----
def get_db():
    return firestore.client(get_firebase_app())


def get_bucket():
    return storage.bucket(app=get_firebase_app())
