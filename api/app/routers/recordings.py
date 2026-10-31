import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..auth import require_auth
from ..db import get_conn

router = APIRouter()


@router.get("/recordings/{sid}")
async def get_recording(sid: str, user_id: int = Depends(require_auth)):
    conn = get_conn()
    call = conn.execute(
        "SELECT * FROM calls WHERE recording_sid = ? AND user_id = ?", (sid, user_id)
    ).fetchone()
    conn.close()
    if not call:
        raise HTTPException(status_code=404)

    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Recordings/{sid}.mp3"
    auth = (account_sid, os.environ["TWILIO_AUTH_TOKEN"])

    client = httpx.AsyncClient()
    req = client.build_request("GET", url, auth=auth)
    resp = await client.send(req, stream=True)
    return StreamingResponse(resp.aiter_bytes(), media_type="audio/mpeg")
