import os

from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import Dial, VoiceResponse

from ..db import get_conn
from ..phone import normalize_and_classify
from ..twilio_client import validate_twilio_request

router = APIRouter()


@router.post("/twiml/voice")
async def voice(request: Request):
    form = dict((await request.form()).items())
    await validate_twilio_request(request, form)

    parsed = normalize_and_classify(form.get("To", ""))
    twiml = VoiceResponse()
    if not parsed:
        twiml.say("Invalid number.")
        return Response(content=str(twiml), media_type="text/xml")

    # The Application-level status callback's To isn't reliably the dialed number,
    # so the call row is created here, where To is known for certain, keyed by CallSid.
    call_sid = form.get("CallSid")
    from_field = form.get("From", "")
    user_id = int(from_field.split(":")[1]) if from_field.startswith("client:") else None
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO calls (sid, user_id, to_number, region, status) VALUES (?, ?, ?, ?, 'ringing')",
        (call_sid, user_id, parsed["e164"], parsed["region"]),
    )
    conn.commit()
    conn.close()

    dial = Dial(
        caller_id=os.environ["TWILIO_NUMBER"],
        record="record-from-answer-dual",
        recording_status_callback=f"{os.environ['PUBLIC_URL']}/webhooks/recording",
    )
    dial.number(parsed["e164"])
    twiml.append(dial)
    return Response(content=str(twiml), media_type="text/xml")
