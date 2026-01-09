# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import argparse
import logging
import os
import sys

from ._version import __version__

logo = r"""                            

     _ __ ___   ___ _ __ ___ _   _ _ __ _   _ 
    | '_ ` _ \ / _ \ '__/ __| | | | '__| | | |
    | | | | | |  __/ | | (__| |_| | |  | |_| |
    |_| |_| |_|\___|_|  \___|\__,_|_|   \__, |
                                         __/ |
                                        |___/ 
"""

LEVEL_NAMES = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]

def _parse_and_inject(argv):
    """
    Parse command-line args and apply:
    - Log level flags
    - Token handling from CLI or env
    - Password hashing from CLI or env
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--log-level", choices=LEVEL_NAMES, default="CRITICAL")

    # New: optional CLI password
    parser.add_argument("--password", help="Plain-text password", default=None)

    # New: optional generic --token flag
    parser.add_argument("--token", help="Token for Jupyter server", default=None)

    ns, rest = parser.parse_known_args(argv[1:])
    new_argv = [argv[0]] + rest

    # ----------------------------
    # LOG LEVEL
    # ----------------------------
    level_name = ns.log_level.upper()
    level_no = getattr(logging, level_name, logging.CRITICAL)

    if not any(a.startswith("--ServerApp.log_level") for a in new_argv):
        new_argv.append(f"--ServerApp.log_level={level_no}")
    if not any(a.startswith("--LabApp.log_level") for a in new_argv):
        new_argv.append(f"--LabApp.log_level={level_no}")
    if not any(a.startswith("--Application.log_level") for a in new_argv):
        new_argv.append(f"--Application.log_level={level_no}")

    # ----------------------------
    # TOKEN HANDLING
    # Priority: CLI > ENV > default empty token
    # ----------------------------
    token_from_cli = (
        ns.token or
        next((a.split("=")[1] for a in new_argv if a.startswith("--ServerApp.token=")), None) or
        next((a.split("=")[1] for a in new_argv if a.startswith("--IdentityProvider.token=")), None)
    )

    token_from_env = os.getenv("MERCURY_TOKEN")

    if token_from_cli:
        # User provided token
        new_argv.append(f"--IdentityProvider.token='{token_from_cli}'")
    elif token_from_env:
        new_argv.append(f"--IdentityProvider.token='{token_from_env}'")
    else:
        # Default behavior: disable token
        new_argv.append("--IdentityProvider.token=''")

    # ----------------------------
    # PASSWORD HANDLING
    # Priority: CLI > ENV
    # ----------------------------
    password = ns.password or os.getenv("MERCURY_PASSWORD")

    if password:
        # Avoid duplicate password injection
        already_set = any(
            a.startswith("--IdentityProvider.hashed_password") or
            a.startswith("--ServerApp.password")
            for a in new_argv
        )

        if not already_set:
            try:
                from jupyter_server.auth import passwd as _passwd
            except ImportError:
                _passwd = None

            if _passwd is None:
                logging.warning(
                    "Password support unavailable: cannot import passwd() hashing function."
                )
            else:
                hashed = _passwd(password)
                new_argv.append(f"--IdentityProvider.hashed_password='{hashed}'")
                new_argv.append(f"--ServerApp.password='{hashed}'")


    # ----------------------------
    # MERCURY_APP: KEEP SESSION (from ENV)
    # Priority: existing CLI/config > env
    # ----------------------------
    keep_session_env = os.getenv("MERCURY_KEEP_SESSION")
    keep_session_already_set = any(
        a.startswith("--MercuryApp.keepSession")
        or a.startswith("--keep-session")
        for a in new_argv
    )

    if keep_session_env is not None and not keep_session_already_set:
        # Normalize env to bool-like
        val = str(keep_session_env).strip().lower()
        if val in ("1", "true", "yes", "on", "True"):
            new_argv.append("--MercuryApp.keepSession=True")
        elif val in ("0", "false", "no", "off", "False"):
            new_argv.append("--MercuryApp.keepSession=False")
        else:
            logging.warning(
                "Invalid MERCURY_KEEP_SESSION value %r, expected True/False/1/0. Ignoring.",
                keep_session_env,
            )

    # ----------------------------
    # MERCURY_APP: TIMEOUT (from ENV)
    # Priority: existing CLI/config > env
    # ----------------------------
    timeout_env = os.getenv("MERCURY_TIMEOUT")
    timeout_already_set = any(
        a.startswith("--MercuryApp.timeout") or a.startswith("--timeout=")
        for a in new_argv
    )

    if timeout_env and not timeout_already_set:
        try:
            timeout_int = int(timeout_env)
            if timeout_int < 0:
                raise ValueError("timeout must be >= 0")
        except ValueError:
            logging.warning(
                "Invalid MERCURY_TIMEOUT value %r, expected non-negative integer seconds. Ignoring.",
                timeout_env,
            )
        else:
            new_argv.append(f"--MercuryApp.timeout={timeout_int}")

    # ----------------------------
    # XSRF HANDLING
    # Disable XSRF only when server is public:
    # - no token (empty)
    # - no password
    # ----------------------------

    def _get_arg_value(prefix: str):
        for a in new_argv:
            if a.startswith(prefix):
                return a.split("=", 1)[1]
        return None

    # Detect "no token" after your injection
    # You inject: --IdentityProvider.token=''  OR --IdentityProvider.token='<token>'
    idp_token_val = _get_arg_value("--IdentityProvider.token=")
    srv_token_val = _get_arg_value("--ServerApp.token=")

    # Normalize: treat '' or "" as empty
    def _is_empty_token(v):
        if v is None:
            return True
        v = v.strip()
        return v in ("''", '""', "''\n", '""\n', "")  # be defensive

    token_is_empty = _is_empty_token(idp_token_val) and _is_empty_token(srv_token_val)

    # Detect if password is set (either hashed_password or ServerApp.password)
    password_is_set = any(
        a.startswith("--IdentityProvider.hashed_password=") or a.startswith("--ServerApp.password=")
        for a in new_argv
    )

    disable_xsrf_already_set = any(
        a.startswith("--ServerApp.disable_check_xsrf=") for a in new_argv
    )

    if token_is_empty and not password_is_set and not disable_xsrf_already_set:
        new_argv.append("--ServerApp.disable_check_xsrf=True")

    # ----------------------------
    # OTHER DEFAULTS
    # ----------------------------
    new_argv.append("--ContentsManager.allow_hidden=True")
    new_argv.append("--MappingKernelManager.default_kernel_name='python3'")

    # Build ServerApp.tornado_settings if not already provided
    tornado_already_set = any(
        a.startswith("--ServerApp.tornado_settings") for a in new_argv
    )

    if not tornado_already_set:
        # Base tornado settings: enable gzip compression
        tornado_settings = {
            "compress_response": True,
        }

        # Optional: allow embedding in iframes based on MERCURY_IFRAME_ALLOW
        #
        # Examples:
        #   MERCURY_IFRAME_ALLOW="*"                         -> frame-ancestors *
        #   MERCURY_IFRAME_ALLOW="https://docs.foo.com"      -> frame-ancestors https://docs.foo.com
        #   MERCURY_IFRAME_ALLOW="https://a.com, https://b.com"
        #       -> frame-ancestors https://a.com https://b.com
        iframe_allow = os.getenv("MERCURY_IFRAME_ALLOW")

        if iframe_allow:
            # Normalize env into space-separated origins
            origins = " ".join(iframe_allow.replace(",", " ").split())
            if origins:
                csp_value = f"frame-ancestors {origins}"
                tornado_settings["headers"] = {
                    "Content-Security-Policy": csp_value
                }

                # 🔑 Make XSRF cookie usable from third-party iframe
                # Tornado expects *lowercase* keys here.
                tornado_settings["xsrf_cookie_kwargs"] = {
                    "samesite": "None",
                    "secure": True,
                }

                # Optional but nice: align IdentityProvider cookie options too
                cookie_opts_already_set = any(
                    a.startswith("--IdentityProvider.cookie_options")
                    for a in new_argv
                )
                if not cookie_opts_already_set:
                    cookie_opts = {"SameSite": "None", "Secure": True}
                    new_argv.append(
                        f"--IdentityProvider.cookie_options={cookie_opts!r}"
                    )

        new_argv.append(f"--ServerApp.tornado_settings={tornado_settings!r}")

    return new_argv

def main(argv=None):
    if argv is None:
        argv = sys.argv
    print(logo)
    print(f"Version: {__version__}")
    sys.argv = _parse_and_inject(argv)
    from mercury_app.app import main as _app_main
    return _app_main()

if __name__ == "__main__":
    raise SystemExit(main())
