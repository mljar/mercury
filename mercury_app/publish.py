"""Interactive publishing, independent of the notebook server startup path."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

from .platform_client import ApiError, PlatformClient, PublishError, authenticate

STATE_FILE = ".mercury-publish.json"
LOCK_FILE = ".mercury-publish.lock"
PLATFORM_URL = "https://platform.mljar.com"
HOSTING_DOMAIN = "ismvp.org"
EXCLUDED_DIRS = {"venv", "env", "node_modules", "__pycache__", "build", "dist"}
EXCLUDED_FILES = {
    "credentials.json",
    "secrets.json",
    "secrets.toml",
    "id_rsa",
    "id_ed25519",
}
SLUG = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


class Cancelled(Exception):
    pass


def ask(question):
    answer = question.ask()
    if answer is None:
        raise Cancelled()
    return answer


def safe_name(name):
    path = PurePosixPath(name)
    return (
        bool(name)
        and not path.is_absolute()
        and "\\" not in name
        and all(
            part not in {".", ".."}
            and not part.startswith(".")
            and all(ord(char) >= 32 and ord(char) != 127 for char in part)
            for part in name.split("/")
        )
        and all(name.split("/"))
    )


def candidates(root):
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            name
            for name in dirs
            if not name.startswith(".")
            and name not in EXCLUDED_DIRS
            and not (Path(directory) / name).is_symlink()
            and not (Path(directory) / name / "pyvenv.cfg").exists()
        )
        for name in sorted(names):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if (
                safe_name(relative)
                and path.is_file()
                and not path.is_symlink()
                and name.lower() not in EXCLUDED_FILES
                and path.suffix.lower()
                not in {".pem", ".key", ".p12", ".pfx", ".pyc", ".env"}
            ):
                files.append(relative)
    return sorted(files)


def checked_path(root, name):
    if not isinstance(name, str) or not safe_name(name):
        raise PublishError("Publish state contains an unsafe file path.")
    path = root
    for part in name.split("/"):
        path = path / part
        if path.is_symlink():
            raise PublishError(f"Symbolic links cannot be uploaded: {name}")
    if not path.is_file() or root not in path.resolve().parents:
        raise PublishError(f"Selected file is missing or outside the project: {name}")
    return path


def load_state(root):
    path = root / STATE_FILE
    if path.is_symlink():
        raise PublishError("Publish state must not be a symbolic link.")
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(state, dict)
            or state.get("version") != 1
            or not isinstance(state.get("site_id"), (str, int))
            or not isinstance(state.get("platform_url"), str)
            or not isinstance(state.get("files"), list)
            or not all(
                isinstance(name, str) and safe_name(name) for name in state["files"]
            )
            or not isinstance(state.get("uploaded_files", {}), dict)
        ):
            raise ValueError()
        return state
    except (ValueError, OSError):
        raise PublishError(
            f"Cannot read {STATE_FILE}. Repair it or move it aside to configure a new deployment."
        ) from None


def save_state(root, state):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=root, prefix=STATE_FILE + ".", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(state, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / STATE_FILE)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


@contextmanager
def publish_lock(root):
    lock = root / LOCK_FILE
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise PublishError(
            f"Another publish may be running. If it has stopped, remove {LOCK_FILE} and retry."
        ) from None
    os.close(descriptor)
    try:
        yield
    finally:
        lock.unlink()


def site_url(site):
    domain = (
        site.get("full_domain")
        or f"{site.get('subdomain', '')}.{site.get('domain', '')}"
    )
    if not isinstance(domain, str) or not all(
        SLUG.fullmatch(part) for part in domain.split(".")
    ):
        raise PublishError("The platform returned an invalid website address.")
    return "https://" + domain


def choose_slug(ui, default=""):
    return ask(
        ui.text(
            "Subdomain:",
            default=default,
            validate=lambda value: (
                True
                if SLUG.fullmatch(value)
                else "Use 1–63 lowercase letters, digits or hyphens; no leading/trailing hyphen."
            ),
        )
    )


def file_picker(ui, root, state):
    available = candidates(root)
    if not available:
        raise PublishError("No publishable files found in the project directory.")
    previous = set(state.get("files", []))
    missing = previous - set(available)
    if missing:
        print(
            "Previously selected files are missing or excluded: "
            + ", ".join(sorted(missing))
        )
        print("Remote files are not deleted by publishing.")
    choices = []
    for name in available:
        size = checked_path(root, name).stat().st_size
        default = (
            name in previous
            if state
            else (
                name.endswith(".ipynb")
                or name in {"requirements.txt", "runtime.txt", "config.toml"}
            )
        )
        choices.append(
            ui.Choice(f"{name} ({size:,} bytes)", value=name, checked=default)
        )
    selected = ask(
        ui.checkbox(
            "Select files to publish (Space to select, Enter to continue):",
            choices=choices,
            validate=lambda values: (
                True
                if any(name.endswith(".ipynb") for name in values)
                else "Select at least one notebook (.ipynb)."
            ),
        )
    )
    if not selected or not any(name.endswith(".ipynb") for name in selected):
        raise PublishError("Select at least one notebook (.ipynb).")
    if any(name not in available for name in selected):
        raise PublishError("File selection contains an unavailable file.")
    if "requirements.txt" not in selected:
        print(
            "No requirements.txt selected. Your app may need one to install its dependencies."
        )
    return selected


def publish(root, ui, open_browser=True, timeout=300):
    state = load_state(root)
    base_url = state.get(
        "platform_url", os.environ.get("MLJAR_PLATFORM_BASE_URL", PLATFORM_URL)
    )
    print(f"Sign in to {base_url}")
    token = authenticate(base_url, open_browser=open_browser, timeout=timeout)
    client = PlatformClient(base_url, token)
    print("Signed in.")
    site = None
    if state:
        site = next(
            (
                item
                for item in client.list_sites()
                if str(item.get("id")) == str(state["site_id"])
            ),
            None,
        )
        if site is None:
            raise PublishError(
                "The saved website is missing or inaccessible to this account. No new website was created."
            )
        url = site_url(site)
        print(f"Existing website: {url}")
        if not ask(ui.confirm("Update this website?", default=True)):
            raise Cancelled()
    else:
        title = ask(
            ui.text(
                "Website title:",
                default=root.name,
                validate=lambda value: bool(value.strip()) or "Enter a title.",
            )
        ).strip()
        domain = os.environ.get("MLJAR_PLATFORM_DEFAULT_DOMAIN", HOSTING_DOMAIN)
        if not all(SLUG.fullmatch(part) for part in domain.split(".")):
            raise PublishError("Invalid hosting domain configuration.")
        suggestion = (
            re.sub(r"[^a-z0-9-]+", "-", root.name.lower()).strip("-")[:63].rstrip("-")
        )
        slug = choose_slug(ui, suggestion)
        url = f"https://{slug}.{domain}"
        print(f"Website: {url}\nVisibility: public")

    selected = file_picker(ui, root, state)
    manifest = {}
    # Copy each selected file to a disk-backed temporary snapshot so hashes,
    # sizes and uploaded bytes agree even if an editor changes the source later.
    with tempfile.TemporaryDirectory(prefix="mercury-publish-") as staging:
        for index, name in enumerate(selected):
            digest = hashlib.sha256()
            size = 0
            with checked_path(root, name).open("rb") as source, (
                Path(staging) / str(index)
            ).open("wb") as dest:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
                    dest.write(chunk)
            manifest[name] = {"sha256": digest.hexdigest(), "size": size}
        print(f"\nDestination: {url}")
        print(
            "Visibility: "
            + (
                "public"
                if site is None or site.get("is_public") is True
                else "check existing access settings on the platform"
            )
        )
        print(
            f"Files: {len(selected)} | Total: {sum(item['size'] for item in manifest.values()):,} bytes"
        )
        for name in selected:
            previous = state.get("uploaded_files", {}).get(name)
            status = (
                "unchanged"
                if previous == manifest[name]
                else "changed" if previous else "new"
            )
            print(f"  {name} ({manifest[name]['size']:,} bytes, {status})")
        print(
            "Only these files will be uploaded. Notebook outputs, data and configuration may contain sensitive information."
        )
        print(
            "Existing remote files with these names will be overwritten; other remote files are not deleted."
        )
        if not ask(ui.confirm("Publish these files?", default=False)):
            raise Cancelled()
        if site is None:
            while True:
                try:
                    site = client.create_site(title, slug, domain)
                    break
                except ApiError as exc:
                    if (
                        exc.status not in (400, 409)
                        or "subdomain" not in json.dumps(exc.payload).lower()
                    ):
                        raise
                    print("The platform rejected this subdomain. Choose another.")
                    slug = choose_slug(ui)
                    print(f"Website: https://{slug}.{domain} (public)")
                    if not ask(ui.confirm("Publish to this address?", default=False)):
                        raise Cancelled()
            if not isinstance(site, dict) or site.get("id") is None:
                raise PublishError(
                    "The platform did not return a website ID. Check the platform before retrying."
                )
            state = {
                "version": 1,
                "platform_url": base_url,
                "site_id": site["id"],
                "files": [],
            }
            # Persist the ID immediately: retry must not create another site.
            try:
                save_state(root, state)
            except OSError:
                raise PublishError(
                    f"Website created (ID {site['id']}), but local deployment state could not be saved. "
                    "Check your project permissions and the platform before retrying to avoid creating a duplicate."
                ) from None
        state.update(app_url=site_url(site), files=selected, pending_upload=manifest)
        save_state(root, state)
        for index, name in enumerate(selected):
            print(f"Uploading {index + 1}/{len(selected)}: {name}", flush=True)
            try:
                with (Path(staging) / str(index)).open("rb") as source:
                    client.upload(site["id"], name, source, manifest[name]["size"])
            except PublishError as exc:
                raise PublishError(
                    f"Upload failed for {name}: {exc} Run mercury publish again to retry this website."
                ) from None
        state.update(
            uploaded_files=manifest,
            last_successful_publish=datetime.now(timezone.utc).isoformat(),
        )
        state.pop("pending_upload", None)
        save_state(root, state)
    print(f"\nUpload complete. Website: {state['app_url']}")
    print("The platform may still need to install dependencies or restart the app.")
    print(f"Deployment saved in {STATE_FILE}. Run mercury publish again to update.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mercury publish", description="Publish notebooks to MLJAR Platform."
    )
    parser.add_argument(
        "--working-dir",
        default=".",
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Print the sign-in URL instead of opening a browser",
    )
    parser.add_argument(
        "--login-timeout",
        type=int,
        default=300,
        help="Sign-in timeout in seconds (default: 300)",
    )
    args = parser.parse_args(argv)
    try:
        root = Path(args.working_dir).expanduser().resolve()
        if not root.is_dir():
            raise PublishError("Working directory does not exist.")
        if args.login_timeout <= 0:
            raise PublishError("Login timeout must be positive.")
        if not sys.stdin.isatty():
            raise PublishError(
                "Publishing requires an interactive terminal. Run mercury publish in your terminal."
            )
        import questionary

        with publish_lock(root):
            publish(root, questionary, not args.no_browser, args.login_timeout)
        return 0
    except (Cancelled, KeyboardInterrupt, EOFError):
        print(
            "\nPublish cancelled. Any previously uploaded files remain on the platform."
        )
        return 130
    except (PublishError, OSError) as exc:
        print(f"Publish failed: {exc}", file=sys.stderr)
        return 1
