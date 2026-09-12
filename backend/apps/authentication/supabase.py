import os
import json
import base64
import logging
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)
User = get_user_model()

class SupabaseAuthentication(BaseAuthentication):
    """
    DRF Authentication Backend for Supabase Auth JWTs.
    Extracts the Bearer JWT token, decodes user metadata,
    and isolates records by user.
    """
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        token_parts = token.split(".")
        if len(token_parts) != 3:
            return None

        try:
            # Decode JWT payload safely without requiring external library
            payload_segment = token_parts[1]
            padded = payload_segment + "=" * ((4 - len(payload_segment) % 4) % 4)
            payload_json = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
            payload = json.loads(payload_json)

            sub = payload.get("sub")
            email = payload.get("email") or f"{sub}@supabase.user"
            
            if not sub:
                return None

            user_metadata = payload.get("user_metadata", {})
            first_name = user_metadata.get("first_name") or user_metadata.get("name", "").split(" ")[0] or "Supabase"
            last_name = user_metadata.get("last_name") or "User"

            user, _ = User.objects.get_or_create(
                username=sub,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                }
            )
            return (user, token)
        except Exception as e:
            logger.warning("Supabase JWT decoding fell back: %s", str(e))
            return None
