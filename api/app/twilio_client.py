import os

from twilio.request_validator import RequestValidator
from twilio.rest import Client

client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
validator = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"])


async def validate_twilio_request(request, form: dict):
    # PUBLIC_URL is explicit, not derived from request headers, since a proxy can misreport scheme/host.
    url = f"{os.environ['PUBLIC_URL']}{request.url.path}"
    if request.url.query:
        url += f"?{request.url.query}"
    signature = request.headers.get("X-Twilio-Signature", "")
    if not validator.validate(url, form, signature):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="invalid twilio signature")
