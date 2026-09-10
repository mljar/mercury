# Markdown security browser regression

Requires the Playwright Node package and Chromium (or `CHROME_PATH` pointing to
a Chrome installation). Use an isolated local test server with no private data.
Run from the repository root with Mercury's Python environment active:

```bash
python -m mercury_app --working-dir=mercury/tests/browser --keep-session=True --ServerApp.ip=127.0.0.1 --ServerApp.port=18765 --ServerApp.port_retries=0 --ServerApp.open_browser=False
```

In another terminal:

```bash
node mercury/tests/browser/markdown-security.cjs
```

The test submits content in browser A, verifies rendering in independent browser
B, then opens a third context to verify retained output for a late joiner. It
asserts a shared kernel PID and zero dialogs for benign content, chat HTML,
streamed HTML split inside an event attribute, script blocks, and `mr.Markdown`.

`MERCURY_TEST_URL` overrides the app URL. Set `EXPECT_XSS=1` only when validating
unpatched Mercury: the test then requires cross-viewer alert execution. Always
start with a fresh server/kernel, since shared sessions retain earlier messages.
Stop the server after testing. These are real alert payloads; do not serve the
fixture publicly.

Python regressions, including subsequent `.text` assignments and cached reuse:

```bash
python -m pytest mercury/tests/test_markdown_security.py -q
```
