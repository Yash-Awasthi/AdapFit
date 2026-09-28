"""Crash reports from the app: logged, and forwarded to Sentry when SENTRY_DSN is set.

Public, because the app can crash before sign-in; the rate limiter caps it per address.
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger("adapfit.client_errors")


class ClientError(BaseModel):
    message: str = Field(max_length=500)
    stack: str = Field("", max_length=4000)
    fatal: bool = False
    platform: str = Field("", max_length=20)
    version: str = Field("", max_length=40)


@router.post("/client-errors", status_code=204)
async def report_client_error(err: ClientError):
    logger.error("app %s %s%s: %s\n%s", err.platform, err.version, " fatal" if err.fatal else "",
                 err.message, err.stack)
    try:
        import sentry_sdk
        with sentry_sdk.new_scope() as scope:
            scope.set_tag("source", "app")
            scope.set_tag("platform", err.platform)
            scope.set_tag("app_version", err.version)
            scope.set_extra("stack", err.stack)
            scope.level = "fatal" if err.fatal else "error"
            sentry_sdk.capture_message(err.message)
    except ImportError:
        pass
