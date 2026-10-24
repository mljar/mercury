"""Exercise notebook access through real HTTP, Jupyter auth, and a contents manager."""

import json
import tempfile
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlencode

import nbformat
from jupyter_server.auth import PasswordIdentityProvider, passwd
from jupyter_server.auth.authorizer import AllowAllAuthorizer
from jupyter_server.auth.login import LoginFormHandler
from jupyter_server.services.contents.filemanager import FileContentsManager
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from mercury_app.block_handler import BlockedHandler
from mercury_app.custom_contents_handler import MercuryContentsHandler


class XSRFTokenHandler(RequestHandler):
    """Test-only stand-in for the cookie issued by the login page."""

    def get(self):
        self.write(self.xsrf_token)


class DenyContentsAuthorizer(AllowAllAuthorizer):
    def is_authorized(self, handler, user, action, resource):
        return resource != "contents"


class TestMercuryContentsHandler(AsyncHTTPTestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="mercury-contents-test-")
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.notebook = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_code_cell(
                    source="secret = 'SOURCE_CANARY'",
                    outputs=[
                        nbformat.v4.new_output(
                            "stream", name="stdout", text="OUTPUT_CANARY"
                        )
                    ],
                )
            ]
        )
        self.paths = ("app.ipynb", ".ipynb_checkpoints/app-checkpoint.ipynb")
        for path in self.paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            nbformat.write(self.notebook, target)
        self.original = (self.root / "app.ipynb").read_bytes()
        super().setUp()

    def get_app(self):
        self.identity = PasswordIdentityProvider(token="", hashed_password="")
        return Application(
            [
                (r"/prefix/login", LoginFormHandler),
                (r"/prefix/test-xsrf", XSRFTokenHandler),
                (r"/prefix/api/contents/(.*\.ipynb)", MercuryContentsHandler),
                (r"/prefix/api/contents(?:/.*)?", BlockedHandler),
            ],
            identity_provider=self.identity,
            authorizer=AllowAllAuthorizer(identity_provider=self.identity),
            contents_manager=FileContentsManager(
                root_dir=str(self.root), allow_hidden=True
            ),
            # Keep the permissive Jupyter default: the handler must enforce auth.
            allow_unauthenticated_access=True,
            cookie_secret="test-only-cookie-secret",
            xsrf_cookies=True,
            base_url="/prefix/",
            login_url="/prefix/login",
        )

    @staticmethod
    def cookies(response):
        cookies = SimpleCookie()
        for value in response.headers.get_list("Set-Cookie"):
            cookies.load(value)
        return cookies

    def xsrf_headers(self):
        response = self.fetch("/prefix/test-xsrf")
        cookie = self.cookies(response)["_xsrf"]
        return {
            "Cookie": cookie.OutputString(attrs=[]),
            "X-XSRFToken": response.body.decode(),
        }

    def read_notebook(self, method, headers=None, path="app.ipynb"):
        kwargs = {"body": '{"content": "MUST_NOT_BE_SAVED"}'} if method == "PUT" else {}
        return self.fetch(
            "/prefix/api/contents/" + path,
            method=method,
            headers=headers or {},
            follow_redirects=False,
            **kwargs,
        )

    def assert_notebook(self, response):
        assert response.code == 200, response.body
        content = json.loads(response.body)["content"]
        assert content["cells"][0]["source"] == "secret = 'SOURCE_CANARY'"
        assert content["cells"][0]["outputs"][0]["text"] == "OUTPUT_CANARY"
        assert (self.root / "app.ipynb").read_bytes() == self.original

    def test_anonymous_requests_cannot_read_token_or_password_protected_notebooks(self):
        for mode in ("token", "password"):
            self.identity.token = "test-token" if mode == "token" else ""
            self.identity.hashed_password = (
                passwd("test-password") if mode == "password" else ""
            )
            # A valid XSRF token must not substitute for authentication on PUT.
            headers = self.xsrf_headers()
            for path in self.paths:
                for method in ("GET", "PUT"):
                    with self.subTest(mode=mode, path=path, method=method):
                        response = self.read_notebook(method, headers, path)
                        assert response.code == 403, response.body
                        assert b"SOURCE_CANARY" not in response.body
                        assert b"OUTPUT_CANARY" not in response.body

    def test_valid_token_allows_reads_and_put_does_not_save(self):
        self.identity.token = "test-token"
        for method in ("GET", "PUT"):
            with self.subTest(method=method):
                self.assert_notebook(
                    self.read_notebook(method, {"Authorization": "token test-token"})
                )

    def test_password_login_cookie_allows_reads_and_put_does_not_save(self):
        self.identity.hashed_password = passwd("test-password")
        headers = self.xsrf_headers()
        response = self.fetch(
            "/prefix/login",
            method="POST",
            headers=headers,
            body=urlencode({"password": "test-password"}),
            follow_redirects=False,
        )
        assert response.code == 302, response.body
        login_cookies = self.cookies(response)
        assert login_cookies
        headers["Cookie"] += "; " + "; ".join(
            cookie.OutputString(attrs=[]) for cookie in login_cookies.values()
        )
        for method in ("GET", "PUT"):
            with self.subTest(method=method):
                self.assert_notebook(self.read_notebook(method, headers))

    def test_public_notebook_reads_still_work(self):
        for method in ("GET", "PUT"):
            with self.subTest(method=method):
                self.assert_notebook(self.read_notebook(method, self.xsrf_headers()))

    def test_public_put_still_requires_xsrf(self):
        response = self.read_notebook("PUT")
        assert response.code == 403
        assert (self.root / "app.ipynb").read_bytes() == self.original

    def test_authenticated_requests_still_require_authorization(self):
        self.identity.token = "test-token"
        self._app.settings["authorizer"] = DenyContentsAuthorizer(
            identity_provider=self.identity
        )
        for method in ("GET", "PUT"):
            with self.subTest(method=method):
                response = self.read_notebook(
                    method, {"Authorization": "token test-token"}
                )
                assert response.code == 403, response.body
                assert b"SOURCE_CANARY" not in response.body

    def test_notebook_mutations_remain_forbidden_even_with_valid_credentials(self):
        self.identity.token = "test-token"
        for method in ("POST", "PATCH", "DELETE"):
            with self.subTest(method=method):
                kwargs = {"body": "{}"} if method != "DELETE" else {}
                response = self.fetch(
                    "/prefix/api/contents/app.ipynb",
                    method=method,
                    headers={"Authorization": "token test-token"},
                    **kwargs,
                )
                assert response.code == 403, response.body
                assert (self.root / "app.ipynb").read_bytes() == self.original
