# ============================================================
# firebase_admin_setup.py
# Initialises Firebase Admin SDK for server-side access to 
# Firestore (database) and Cloud Storage (file storage).
# Imported by app.py to provide db and bucket objects.
# ============================================================

# ---- Imports ----
import firebase_admin
from firebase_admin import credentials, firestore, storage

# ---- Firebase Initialization ----
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'dissertation-4cc1f.firebasestorage.app'
    })

# ---- Export Firestore and Storage Clients ----
db = firestore.client()
bucket = storage.bucket()