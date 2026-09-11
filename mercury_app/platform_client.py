"""MLJAR Platform browser authentication and file upload protocol.

Adapted from mljar-supervised's publisher, without its AutoML dependency.
"""

import hashlib
import http.client
import json
import platform
import socket
import time
import uuid
import webbrowser
from urllib import error, parse, request

from ._version import __version__


class PublishError(Exception):
    """An actionable publishing failure, safe to display in the terminal."""


class ApiError(PublishError):
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload
        super().__init__(f"Platform request failed (HTTP {status}).")


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the login token to another host.
        return None


def https_url(value):
    parsed = parse.urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise PublishError(
            "The platform and storage URLs must use HTTPS without credentials."
        )
    return parsed


class PlatformClient:
    def __init__(self, base_url, token=None):
        parsed = https_url(base_url)
        if parsed.query or parsed.path not in ("", "/"):
            raise PublishError("Platform address must be an HTTPS origin.")
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method, path, data=None):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(
            self.base_url + path, data=body, headers=headers, method=method
        )
        try:
            with request.build_opener(NoRedirect()).open(req, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except error.HTTPError as exc:
            try:
                payload = json.loads(exc.read())
            except (ValueError, OSError):
                payload = {}
            # Raw server messages can contain signed URLs or credentials.
            raise ApiError(exc.code, payload) from None
        except (error.URLError, OSError, http.client.HTTPException):
            raise PublishError(
                "Could not reach the platform. Check your connection and retry."
            ) from None
        except ValueError:
            raise PublishError("The platform returned an invalid response.") from None

    def list_sites(self):
        result, seen = [], set()
        path = "/api/sites/"
        while path:
            if path in seen:
                raise PublishError("The platform returned repeated website pages.")
            seen.add(path)
            payload = self.request("GET", path)
            sites = payload.get("results") if isinstance(payload, dict) else payload
            if not isinstance(sites, list) or not all(
                isinstance(site, dict) for site in sites
            ):
                raise PublishError("The platform returned an invalid website list.")
            result.extend(sites)
            next_url = payload.get("next") if isinstance(payload, dict) else None
            path = None
            if next_url:
                target = parse.urlsplit(
                    parse.urljoin(self.base_url + "/api/sites/", next_url)
                )
                if (
                    target.scheme + "://" + target.netloc != self.base_url
                    or target.path != "/api/sites/"
                    or target.fragment
                ):
                    raise PublishError(
                        "The platform returned an invalid website page URL."
                    )
                path = target.path + ("?" + target.query if target.query else "")
        return result

    def create_site(self, title, subdomain, domain):
        return self.request(
            "POST",
            "/api/sites/",
            {
                "title": title,
                "subdomain": subdomain,
                "domain": domain,
                "is_public": True,
            },
        )

    def upload(self, site_id, filename, stream, size):
        parts = [
            parse.quote(str(value), safe="") for value in (site_id, filename, size)
        ]
        payload = self.request("GET", "/api/presigned-url-put/" + "/".join(parts))
        if not isinstance(payload, dict) or not isinstance(payload.get("url"), str):
            raise PublishError("The platform did not return an upload URL.")
        target = https_url(payload["url"])
        connection = http.client.HTTPSConnection(
            target.hostname, target.port, timeout=120
        )
        try:
            # Stream file bytes; no platform bearer token or forced content type.
            path = parse.urlunsplit(("", "", target.path or "/", target.query, ""))
            connection.request(
                "PUT", path, body=stream, headers={"Content-Length": str(size)}
            )
            response = connection.getresponse()
            response.read()
            if not 200 <= response.status < 300:
                raise PublishError(
                    f"Storage upload failed (HTTP {response.status}). Retry publishing."
                )
        except (OSError, http.client.HTTPException):
            raise PublishError(
                "Storage connection failed. Retry publishing to the same website."
            ) from None
        finally:
            connection.close()
        self.request(
            "POST",
            "/api/file-uploaded",
            {
                "site_id": site_id,
                "filename": filename,
                "filesize": size,
            },
        )


def authenticate(base_url, open_browser=True, timeout=300):
    client = PlatformClient(base_url)
    install_id = f"mercury-{uuid.uuid4().hex}"
    host = socket.gethostname()
    system = platform.system().lower() or "python"
    device = {
        "device_install_id": install_id,
        "platform": system,
        "app_version": __version__,
        "device_label": host,
        "client_fingerprint_hash": hashlib.sha256(
            f"{install_id}|{system}|{host}".encode()
        ).hexdigest(),
    }
    session = client.request("POST", "/api/app/auth/session/start", device)
    if (
        not isinstance(session, dict)
        or not session.get("session_id")
        or not session.get("poll_token")
    ):
        raise PublishError("The platform did not return a valid login session.")
    session_id, poll_token = session["session_id"], session["poll_token"]
    login_url = (
        client.base_url
        + "/app/desktop-login?"
        + parse.urlencode(
            {
                "session_id": session_id,
                "auth_mode": "signin",
            }
        )
    )
    opened = False
    if open_browser:
        try:
            opened = webbrowser.open(login_url)
        except webbrowser.Error:
            pass
    if not opened:
        print("Open this URL in your browser to sign in:\n" + login_url)
    print("Waiting for browser sign-in (Ctrl+C to cancel)…")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.request(
            "GET",
            "/api/app/auth/session/status?"
            + parse.urlencode(
                {
                    "session_id": session_id,
                    "poll_token": poll_token,
                }
            ),
        )
        if not isinstance(status, dict):
            raise PublishError("The platform returned an invalid login status.")
        if status.get("status") == "completed":
            result = client.request(
                "POST",
                "/api/app/auth/session/exchange",
                {
                    **device,
                    "session_id": session_id,
                    "poll_token": poll_token,
                },
            )
            if not isinstance(result, dict) or not result.get("token"):
                raise PublishError("Sign-in completed, but no token was returned.")
            return result["token"]
        if status.get("status") in {"expired", "consumed", "denied", "cancelled"}:
            raise PublishError(
                "Sign-in expired or was declined. Run mercury publish again."
            )
        time.sleep(2)
    raise PublishError("Timed out waiting for sign-in. Run mercury publish again.")
