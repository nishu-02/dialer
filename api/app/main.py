import os

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from .db import init_db
from .routers import calls, recordings, session, twiml, voice_token, webhooks

init_db()

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SESSION_SECRET"],
    same_site="lax",
    https_only=os.environ.get("ENV") == "production",
)

app.include_router(session.router, prefix="/api")
app.include_router(voice_token.router, prefix="/api")
app.include_router(calls.router, prefix="/api")
app.include_router(recordings.router, prefix="/api")
app.include_router(twiml.router)
app.include_router(webhooks.router)
