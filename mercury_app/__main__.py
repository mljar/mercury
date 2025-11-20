import os
import sys
import logging
import argparse

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
                try:
                    from notebook.auth import passwd as _passwd
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
    # OTHER DEFAULTS
    # ----------------------------
    new_argv.append("--ContentsManager.allow_hidden=True")
    new_argv.append("--MappingKernelManager.default_kernel_name='python3'")

    return new_argv

def main(argv=None):
    """Console script entrypoint."""
    if argv is None:
        argv = sys.argv
    print(logo)
    print(f"Version: {__version__}")
    sys.argv = _parse_and_inject(argv)
    from mercury_app.app import main as _app_main
    return _app_main()

if __name__ == "__main__":
    raise SystemExit(main())
