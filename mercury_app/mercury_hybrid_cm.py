# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from __future__ import annotations

import posixpath
from datetime import datetime, timezone
from typing import Any, Dict, List

from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel
from jupyter_server.services.contents.manager import ContentsManager
from jupyter_server.utils import ensure_async
from tornado.web import HTTPError


def _now():
    return datetime.now(timezone.utc)


def _norm(path: str) -> str:
    """Jupyter contents paths are POSIX-style and relative to root (no leading slash)."""
    return path.lstrip("/")


class _MemStore:
    """Very small in-memory store for shadow notebooks (path -> model)."""

    def __init__(self):
        self._files: Dict[str, Dict[str, Any]] = {}

    def exists(self, path: str) -> bool:
        return path in self._files

    def get(self, path: str) -> Dict[str, Any]:
        return self._files[path]

    def save_nb(self, path: str, nb_json: Dict[str, Any]) -> Dict[str, Any]:
        model = {
            "type": "notebook",
            "format": "json",
            "path": path,
            "name": posixpath.basename(path),
            "created": _now(),
            "last_modified": _now(),
            "content": nb_json,
            # Extra fields expected by some Jupyter clients
            "mimetype": None,
            "writable": True,
            "size": None,
        }
        self._files[path] = model
        return model

    def delete(self, path: str) -> None:
        self._files.pop(path, None)

    def list_dir(self, dir_path: str) -> Dict[str, Any]:
        """Return a directory model for immediate children of dir_path."""
        prefix = dir_path.rstrip("/") + "/"
        children: List[Dict[str, Any]] = []

        for p, m in self._files.items():
            if p.startswith(prefix):
                # Include only immediate children (no nested paths)
                rest = p[len(prefix):]
                if "/" in rest:
                    continue
                child = {k: v for k, v in m.items() if k != "content"}
                children.append(child)

        return {
            "type": "directory",
            "path": dir_path,
            "name": posixpath.basename(dir_path.rstrip("/")) or "",
            "created": _now(),
            "last_modified": _now(),
            "format": "json",
            "content": children,
            # Extra fields
            "mimetype": None,
            "writable": True,
            "size": None,
        }


class HybridContentsManager(ContentsManager):
    """
    Wraps an existing ContentsManager and redirects all paths under
    shadow prefixes to an in-memory store. All other paths are delegated
    to the real contents manager.

    Shadow roots:
      - '.mercury_sessions'
      - '_mercury_sessions'
    """

    SHADOW_ROOTS = (".mercury_sessions", "_mercury_sessions")

    def __init__(self, real_cm: ContentsManager, **kwargs):
        super().__init__(parent=real_cm.parent, **kwargs)
        self.real_cm = real_cm
        self._mem = _MemStore()
        self._ksm = KernelSpecManager()  # Helper for kernelspec lookup

        # Try to determine the default kernel name from ServerApp / KernelManager.
        # Fall back to KernelSpecManager default (usually 'python3').
        try:
            self._default_kernel = (
                getattr(getattr(self.parent, "kernel_manager", None), "default_kernel_name", None)
                or getattr(self.parent, "default_kernel_name", None)
                or self._ksm.default_kernel_name
            )
        except Exception:
            self._default_kernel = self._ksm.default_kernel_name

        self.log.info(
            "[MercuryHybridCM] active; underlying=%s",
            type(real_cm).__name__,
        )

    # ---------------- helpers ----------------

    @classmethod
    def wrap(cls, cm: ContentsManager) -> "HybridContentsManager":
        return cls(real_cm=cm)

    @staticmethod
    def _is_shadow_root(path: str) -> bool:
        return path in HybridContentsManager.SHADOW_ROOTS

    @staticmethod
    def _is_shadow(path: str) -> bool:
        if path in HybridContentsManager.SHADOW_ROOTS:
            return True
        return any(path.startswith(root + "/") for root in HybridContentsManager.SHADOW_ROOTS)

    def _kernel_exists(self, name: str) -> bool:
        if not name:
            return False
        try:
            self._ksm.get_kernel_spec(name)
            return True
        except NoSuchKernel:
            return False
        except Exception:
            # Be conservative: treat any other failure as "kernel not available"
            return False

    def _ensure_valid_kernelspec(self, nb_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        If the notebook kernelspec is missing or refers to a non-installed kernel,
        rewrite it to the default kernel and update display_name (and language if available).
        """
        if not isinstance(nb_json, dict):
            return nb_json

        md = nb_json.setdefault("metadata", {})
        ks = md.setdefault("kernelspec", {})
        name = ks.get("name")

        if self._kernel_exists(name):
            return nb_json

        # Select fallback kernel
        fallback = self._default_kernel or "python3"

        try:
            spec = self._ksm.get_kernel_spec(fallback)
            display = getattr(spec, "display_name", None) or fallback
        except Exception:
            display = fallback

        # Rewrite kernelspec
        ks["name"] = fallback
        ks["display_name"] = display

        # Optionally align language with kernelspec
        try:
            lang = getattr(spec, "language", None)
            if lang:
                ks["language"] = lang
        except Exception:
            pass

        self.log.warning(
            "[MercuryHybridCM] kernelspec '%s' not found. "
            "Rewriting to default '%s' (%s).",
            name,
            ks.get("name"),
            ks.get("display_name"),
        )

        return nb_json

    # ---------------- core API ----------------

    async def get(self, path: str, content: bool = True, type=None, format=None):
        path = _norm(path)

        if self._is_shadow(path):
            if self._is_shadow_root(path) or path.endswith("/"):
                self.log.debug("[MercuryHybridCM] GET dir (shadow): %s", path)
                return self._mem.list_dir(path.rstrip("/"))

            if not self._mem.exists(path):
                self.log.debug("[MercuryHybridCM] GET (shadow) MISS: %s", path)
                raise HTTPError(404, f"Shadow notebook not found: {path}")

            self.log.debug(
                "[MercuryHybridCM] GET (shadow) HIT: %s content=%s",
                path,
                content,
            )

            model = self._mem.get(path)

            if content:
                # Optionally sanitize kernelspec (same logic as for real notebooks)
                try:
                    if isinstance(model.get("content"), dict):
                        model["content"] = self._ensure_valid_kernelspec(model["content"])
                except Exception as e:
                    self.log.exception(
                        "[MercuryHybridCM] kernelspec sanitize (get shadow) failed for %s: %s",
                        path,
                        e,
                    )
                return model

            # content=False → content key must exist but be None
            out = dict(model)
            out["content"] = None
            out["format"] = None
            return out

        self.log.debug("[MercuryHybridCM] → GET delegate: %s", path)
        model = await ensure_async(
            self.real_cm.get(path, content=content, type=type, format=format)
        )

        # Sanitize kernelspec for real notebooks
        try:
            if content and model.get("type") == "notebook" and isinstance(model.get("content"), dict):
                model["content"] = self._ensure_valid_kernelspec(model["content"])
        except Exception as e:
            self.log.exception(
                "[MercuryHybridCM] kernelspec sanitize (get) failed for %s: %s",
                path,
                e,
            )

        return model

    async def save(self, model: Dict[str, Any], path: str):
        path = _norm(path)

        if self._is_shadow(path):
            if model.get("type") != "notebook" or model.get("format") != "json":
                self.log.warning(
                    "[MercuryHybridCM] SAVE (shadow) rejected non-notebook: %s",
                    path,
                )
                raise HTTPError(400, "Only notebook JSON is supported in the shadow area")

            nb = model.get("content") or {}
            saved = self._mem.save_nb(path, nb)
            self.log.debug("[MercuryHybridCM] SAVE (shadow): %s", path)

            # Validator after SAVE expects: content=None and format=None
            out = {k: v for k, v in saved.items() if k != "content"}
            out["content"] = None
            out["format"] = None
            return out

        # Sanitize kernelspec before persisting so future opens also work
        try:
            if (
                model.get("type") == "notebook"
                and model.get("format") == "json"
                and isinstance(model.get("content"), dict)
            ):
                model = dict(model)  # Shallow copy to avoid mutating caller data
                model["content"] = self._ensure_valid_kernelspec(model["content"])
        except Exception as e:
            self.log.exception(
                "[MercuryHybridCM] kernelspec sanitize (save) failed for %s: %s",
                path,
                e,
            )

        self.log.debug("[MercuryHybridCM] → SAVE delegate: %s", path)
        return await ensure_async(self.real_cm.save(model, path))

    async def delete(self, path: str):
        path = _norm(path)

        if self._is_shadow(path):
            self.log.debug("[MercuryHybridCM] DELETE (shadow): %s", path)

            if self._is_shadow_root(path):
                # Delete all notebooks under this shadow root
                for root in self.SHADOW_ROOTS:
                    if path == root:
                        for p in [
                            p for p in list(self._mem._files.keys())
                            if p.startswith(root + "/")
                        ]:
                            self._mem.delete(p)
                return

            self._mem.delete(path)
            return

        self.log.debug("[MercuryHybridCM] → DELETE delegate: %s", path)
        return await ensure_async(self.real_cm.delete(path))

    async def dir_exists(self, path: str) -> bool:
        path = _norm(path)

        if self._is_shadow_root(path):
            self.log.debug(
                "[MercuryHybridCM] DIR exists (shadow root): %s -> True",
                path,
            )
            return True

        if self._is_shadow(path):
            self.log.debug(
                "[MercuryHybridCM] DIR exists (shadow subdir): %s -> True",
                path,
            )
            return True

        exists = await ensure_async(self.real_cm.dir_exists(path))
        self.log.debug(
            "[MercuryHybridCM] → DIR exists delegate(%s) = %s",
            path,
            exists,
        )
        return exists

    async def file_exists(self, path: str) -> bool:
        path = _norm(path)

        if self._is_shadow(path):
            exists = self._mem.exists(path)
            self.log.debug(
                "[MercuryHybridCM] FILE exists (shadow): %s = %s",
                path,
                exists,
            )
            return exists

        exists = await ensure_async(self.real_cm.file_exists(path))
        self.log.debug(
            "[MercuryHybridCM] → FILE exists delegate(%s) = %s",
            path,
            exists,
        )
        return exists

    # ---------------- checkpoints (shadow: no-op) ----------------

    async def list_checkpoints(self, path: str):
        path = _norm(path)

        if self._is_shadow(path):
            self.log.debug(
                "[MercuryHybridCM] CHECKPOINTS list (shadow): %s -> []",
                path,
            )
            return []

        self.log.debug("[MercuryHybridCM] → CHECKPOINTS list delegate: %s", path)
        return await ensure_async(self.real_cm.list_checkpoints(path))

    async def create_checkpoint(self, path: str):
        path = _norm(path)

        if self._is_shadow(path):
            self.log.debug(
                "[MercuryHybridCM] CHECKPOINT create (shadow): %s -> noop",
                path,
            )
            return {"id": "shadow", "last_modified": _now()}

        self.log.debug("[MercuryHybridCM] → CHECKPOINT create delegate: %s", path)
        return await ensure_async(self.real_cm.create_checkpoint(path))

    async def restore_checkpoint(self, path: str, checkpoint_id: str):
        path = _norm(path)

        if self._is_shadow(path):
            self.log.debug(
                "[MercuryHybridCM] CHECKPOINT restore (shadow): %s %s -> noop",
                path,
                checkpoint_id,
            )
            return

        self.log.debug(
            "[MercuryHybridCM] → CHECKPOINT restore delegate: %s %s",
            path,
            checkpoint_id,
        )
        return await ensure_async(self.real_cm.restore_checkpoint(path, checkpoint_id))

    async def delete_checkpoint(self, path: str, checkpoint_id: str):
        path = _norm(path)

        if self._is_shadow(path):
            self.log.debug(
                "[MercuryHybridCM] CHECKPOINT delete (shadow): %s %s -> noop",
                path,
                checkpoint_id,
            )
            return

        self.log.debug(
            "[MercuryHybridCM] → CHECKPOINT delete delegate: %s %s",
            path,
            checkpoint_id,
        )
        return await ensure_async(self.real_cm.delete_checkpoint(path, checkpoint_id))
