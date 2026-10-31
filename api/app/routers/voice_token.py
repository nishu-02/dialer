import os

from fastapi import APIRouter, Depends
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant

from ..auth import require_auth

router = APIRouter()


@router.get("/voice-token")
def voice_token(user_id: int = Depends(require_auth)):
    token = AccessToken(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_API_KEY_SID"],
        os.environ["TWILIO_API_KEY_SECRET"],
        identity=str(user_id),
        ttl=3600,
    )
    token.add_grant(
        VoiceGrant(outgoing_application_sid=os.environ["TWIML_APP_SID"], incoming_allow=False)
    )
    return {"token": token.to_jwt()}
