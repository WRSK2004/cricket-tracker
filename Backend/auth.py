# ============================================================
# auth.py
# Verifies the Firebase ID token sent by the frontend in the
# "Authorization: Bearer <token>" header and returns the user's
# uid. Endpoints that need a signed-in user depend on
# get_current_user, so the uid can no longer be faked.
# ============================================================

# ---- Imports ----
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

from firebase_admin_setup import get_firebase_app

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


# ---- Current User Dependency ----
def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "You need to be signed in to do that.")
    try:
        decoded = auth.verify_id_token(credentials.credentials, app=get_firebase_app())
    except auth.CertificateFetchError:
        logger.exception("Could not fetch Firebase public keys")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Sign-in check is unavailable. Please try again."
        ) from None
    except (ValueError, auth.InvalidIdTokenError, auth.UserDisabledError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your sign-in has expired. Please sign in again.") from None
    return decoded["uid"]
