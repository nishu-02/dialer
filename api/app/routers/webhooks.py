from fastapi import APIRouter, Request

from ..db import get_conn
from ..phone import normalize_and_classify
from ..twilio_client import validate_twilio_request

router = APIRouter()


@router.post("/webhooks/status")
async def status(request: Request):
    form = dict((await request.form()).items())
    await validate_twilio_request(request, form)

    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    duration = form.get("CallDuration")
    to_number = form.get("To", "")
    # Client identity set in Device.connect's caller shows up as "client:<user_id>" on the From leg.
    from_field = form.get("From", "")
    user_id = int(from_field.split(":")[1]) if from_field.startswith("client:") else None

    conn = get_conn()
    existing = conn.execute("SELECT sid FROM calls WHERE sid = ?", (call_sid,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE calls SET status = ?, duration = ? WHERE sid = ?",
            (call_status, int(duration) if duration else None, call_sid),
        )
    else:
        parsed = normalize_and_classify(to_number) or {"region": "international"}
        conn.execute(
            "INSERT INTO calls (sid, user_id, to_number, region, status, duration) VALUES (?, ?, ?, ?, ?, ?)",
            (call_sid, user_id, to_number, parsed["region"], call_status, int(duration) if duration else None),
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
