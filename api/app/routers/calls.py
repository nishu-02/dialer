from fastapi import APIRouter, Depends

from ..auth import require_auth
from ..db import get_conn

router = APIRouter()


@router.get("/calls")
def list_calls(user_id: int = Depends(require_auth)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM calls WHERE user_id = ? ORDER BY created_at DESC LIMIT 100", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
