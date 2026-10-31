from fastapi import APIRouter, Request

from ..db import get_conn
from ..twilio_client import validate_twilio_request

router = APIRouter()


@router.post("/webhooks/status")
async def status(request: Request):
    form = dict((await request.form()).items())
    await validate_twilio_request(request, form)

    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    duration = form.get("CallDuration")

    conn = get_conn()
    # /twiml/voice always runs before a call can connect, so the row already exists by
    # now; inserting a fallback row here raced it and could win with a blank to_number.
    conn.execute(
        "UPDATE calls SET status = ?, duration = ? WHERE sid = ?",
        (call_status, int(duration) if duration else None, call_sid),
    )
    conn.commit()
    conn.close()
    return None


@router.post("/webhooks/recording")
async def recording(request: Request):
    form = dict((await request.form()).items())
    await validate_twilio_request(request, form)

    conn = get_conn()
    conn.execute(
        "UPDATE calls SET recording_sid = ? WHERE sid = ?",
        (form.get("RecordingSid"), form.get("CallSid")),
    )
    conn.commit()
    conn.close()
    return None
