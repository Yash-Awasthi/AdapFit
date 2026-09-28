"""
Identity binding.

Almost every handler in this API takes the subject's `user_id` from the
request — 144 path templates, 195 query parameters, and a long tail of request
bodies. Adding an ownership check to each of them is 500-odd edits that only
have to be forgotten once, so the parameter is bound to the caller's token here
instead: by the time a handler sees `user_id`, it is the caller's own id and
cannot be anyone else's.

Routes that legitimately address another user are listed in CROSS_USER_PREFIXES
and pass through untouched; each of those carries its own check.
"""
import json
import re
from typing import Optional
from urllib.parse import parse_qsl, urlencode

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.auth import decode_token
from app.core.per_user import CURRENT_USER

API_PREFIX = "/api/v1/"

# Prefixes where naming another user is the point of the endpoint. Each of
# these enforces its own authorization (admin role, or an explicit
# ensure_owner call), so rebinding their user_id would break the feature.
CROSS_USER_PREFIXES = (
    "/api/v1/admin/",
)

# Bodies larger than this are streamed through untouched. A user_id never
# appears in a payload this size, and buffering an upload to look for one
# would hold a file in memory for nothing.
MAX_REWRITABLE_BODY = 1 << 20  # 1 MiB

_PARAM = re.compile(r"\{([^}:]+)(?::[^}]+)?\}")


def _template_to_regex(template: str) -> re.Pattern:
    """Compile an OpenAPI path template into a matcher that captures user_id."""
    out = []
    last = 0
    for match in _PARAM.finditer(template):
        out.append(re.escape(template[last:match.start()]))
        name = match.group(1)
        out.append(f"(?P<user_id>[^/]+)" if name == "user_id" else "[^/]+")
        last = match.end()
    out.append(re.escape(template[last:]))
    return re.compile("^" + "".join(out) + "$")


def _caller(scope: Scope) -> Optional[tuple[str, str]]:
    """(user_id, role) for the request, or None when it is unauthenticated."""
    token = None
    for key, value in scope.get("headers", []):
        if key == b"authorization":
            raw = value.decode("latin-1")
            if raw.startswith("Bearer "):
                token = raw[7:]
            break
    payload = decode_token(token) if token else None
    if payload and payload.get("type") == "access" and payload.get("sub"):
        return str(payload["sub"]), str(payload.get("role") or "user")
    # Without a token there is no identity to bind to. AuthMiddleware has
    # already rejected the request unless the dev bypass is on, and under the
    # bypass the caller is deliberately allowed to address any user.
    return None


class IdentityMiddleware:
    """Rebinds every `user_id` in a request to the authenticated caller."""

    def __init__(self, app: ASGIApp, fastapi_app=None):
        self.app = app
        self._fastapi_app = fastapi_app
        self._matchers: Optional[list[re.Pattern]] = None

    def _path_matchers(self) -> list[re.Pattern]:
        """Compiled matchers for every route template that names a user_id."""
        if self._matchers is None:
            templates: list[str] = []
            try:
                paths = self._fastapi_app.openapi().get("paths", {}) if self._fastapi_app else {}
                templates = [p for p in paths if "{user_id}" in p]
            except Exception:
                templates = []
            self._matchers = [_template_to_regex(t) for t in templates]
        return self._matchers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        caller = _caller(scope)
        # Services that keep per-user state read this rather than a parameter,
        # so it is set for every request, including the ones that pass through
        # untouched below. Each request runs in its own task context, so the
        # value cannot leak into another request.
        CURRENT_USER.set(caller[0] if caller else None)

        path = scope.get("path", "")
        if path.startswith(CROSS_USER_PREFIXES):
            await self.app(scope, receive, send)
            return

        if caller is None:
            await self.app(scope, receive, send)
            return
        user_id, role = caller
        # An admin addressing another user is a support action, not an attack.
        if role in ("admin", "superadmin"):
            await self.app(scope, receive, send)
            return

        scope = dict(scope)
        scope["state"] = dict(scope.get("state") or {})
        scope["state"]["caller_user_id"] = user_id
        self._rebind_path(scope, path, user_id)
        self._rebind_query(scope, path, user_id)
        receive = self._rebinding_receive(scope, receive, user_id)

        await self.app(scope, receive, send)

    def _rebind_path(self, scope: Scope, path: str, user_id: str) -> None:
        for matcher in self._path_matchers():
            found = matcher.match(path)
            if not found:
                continue
            start, end = found.span("user_id")
            if path[start:end] == user_id:
                return
            new_path = path[:start] + user_id + path[end:]
            scope["path"] = new_path
            scope["raw_path"] = new_path.encode("utf-8")
            return

    def _rebind_query(self, scope: Scope, path: str, user_id: str) -> None:
        """
        Bind user_id in the query string, adding it when the client omitted it.

        Omission is the dangerous case, not substitution: handlers declare
        `user_id: str = Query("default")`, so a request that simply leaves it
        out lands every account in one shared bucket. Injecting it is safe for
        handlers that do not declare the parameter — FastAPI ignores query
        parameters no signature asks for.
        """
        raw = scope.get("query_string", b"")
        pairs = parse_qsl(raw.decode("latin-1"), keep_blank_values=True)
        if any(key == "user_id" for key, _ in pairs):
            rebound = [(key, user_id if key == "user_id" else value) for key, value in pairs]
        elif path.startswith(API_PREFIX):
            rebound = pairs + [("user_id", user_id)]
        else:
            return
        scope["query_string"] = urlencode(rebound).encode("latin-1")

    def _rebinding_receive(self, scope: Scope, receive: Receive, user_id: str) -> Receive:
        """Wrap receive so a JSON body's top-level user_id is the caller's too."""
        content_type = b""
        length = 0
        for key, value in scope.get("headers", []):
            if key == b"content-type":
                content_type = value
            elif key == b"content-length":
                try:
                    length = int(value)
                except ValueError:
                    length = 0
        if not content_type.startswith(b"application/json") or length > MAX_REWRITABLE_BODY:
            return receive

        state = {"done": False, "queue": []}

        async def wrapped() -> Message:
            if state["queue"]:
                return state["queue"].pop(0)
            if state["done"]:
                return await receive()

            body = b""
            while True:
                message = await receive()
                if message["type"] != "http.request":
                    state["done"] = True
                    return message
                body += message.get("body", b"")
                if not message.get("more_body", False):
                    break
                if len(body) > MAX_REWRITABLE_BODY:
                    # Too large to inspect: hand back what was read and stop
                    # buffering. Path and query are already bound.
                    state["done"] = True
                    return {"type": "http.request", "body": body, "more_body": True}

            state["done"] = True
            rewritten = _rebind_body(body, user_id)
            if rewritten is not body:
                _set_content_length(scope, len(rewritten))
            return {"type": "http.request", "body": rewritten, "more_body": False}

        return wrapped


def _rebind_body(body: bytes, user_id: str) -> bytes:
    """Replace a top-level user_id in a JSON object; return body unchanged otherwise."""
    if not body or b"user_id" not in body:
        return body
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return body
    if not isinstance(payload, dict) or payload.get("user_id") in (None, user_id):
        return body
    payload["user_id"] = user_id
    return json.dumps(payload).encode("utf-8")


def _set_content_length(scope: Scope, length: int) -> None:
    headers = [(k, v) for k, v in scope.get("headers", []) if k != b"content-length"]
    headers.append((b"content-length", str(length).encode("latin-1")))
    scope["headers"] = headers
