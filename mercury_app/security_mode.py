from __future__ import annotations

from enum import Enum


class SecurityMode(str, Enum):
    JUPYTER_AUTHORING = "jupyter-authoring"
    PUBLIC_APP = "anonymous-firewall"
    AUTHENTICATED_APP = "authenticated-firewall"


def detect_standalone_security_mode(serverapp) -> SecurityMode:
    """Return the effective standalone access mode after traitlets config loads."""
    identity_provider = getattr(serverapp, "identity_provider", None)
    token = getattr(identity_provider, "token", "") or ""
    hashed_password = getattr(identity_provider, "hashed_password", "") or ""
    legacy_password = getattr(serverapp, "password", "") or ""
    if token or hashed_password or legacy_password:
        return SecurityMode.AUTHENTICATED_APP
    return SecurityMode.PUBLIC_APP
