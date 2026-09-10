"""Exercise both public Markdown sinks, including reactive and streaming updates."""

from html.parser import HTMLParser
from importlib import import_module

import pytest
from IPython.display import HTML, Markdown as IPythonMarkdown

from mercury._markdown import render_markdown
from mercury.md import MarkdownWidget

md_module = import_module("mercury.md")
message_module = import_module("mercury.chat.message")

PAYLOADS = [
    '<div>visible<img src=x onerror="alert(1)"></div>',
    '<script>alert(1)</script><p>visible</p>',
    '<svg onload="alert(1)"><script>alert(1)</script></svg>',
    '<a href="jAvAsCrIpT:alert(1)">visible</a>',
    '<a href="java&#x09;script:alert(1)">visible</a>',
    '[visible](javascript:alert%281%29)',
    '<img src="data:image/svg+xml,<svg onload=alert(1)>">',
    '<iframe srcdoc="<script>alert(1)</script>"></iframe>',
    '<div style="position:fixed" onclick="alert(1)">visible</div>',
    '<math><mtext><table><mglyph><style><!--</style><img title="--><img src=x onerror=alert(1)>">',
]


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def assert_safe(html):
    for tag, attrs in Elements(html).elements:
        assert tag not in {"script", "svg", "math", "iframe", "object", "style"}
        assert not any(name.startswith("on") for name in attrs)
        for name in ("src", "href"):
            value = "".join((attrs.get(name) or "").split()).lower()
            assert not value.startswith(("javascript:", "data:", "vbscript:"))


@pytest.mark.parametrize("payload", PAYLOADS)
def test_markdown_creation_and_update(payload):
    widget = MarkdownWidget(payload)
    assert_safe(widget.value)
    widget.text = '**hello**\n\n' + payload
    assert_safe(widget.value)
    assert '<strong style="font-weight: 700;">hello</strong>' in widget.value


@pytest.mark.parametrize("payload", PAYLOADS)
def test_message_creation_replacement_and_streaming(monkeypatch, payload):
    displayed = []
    monkeypatch.setattr(message_module, "display", displayed.append)
    msg = message_module.Message(payload)
    assert isinstance(displayed[-1], HTML)
    assert_safe(displayed[-1].data)
    msg.set_content(markdown="")
    # Attack syntax may be incomplete at any intermediate render.
    for char in payload:
        msg.append_markdown(char)
        assert_safe(displayed[-1].data)
    assert displayed[-1].data == render_markdown(payload)


def test_explicit_unsafe_modes_and_raw_html(monkeypatch):
    payload = PAYLOADS[0]
    assert 'onerror=' in MarkdownWidget(payload, unsafe_allow_html=True).value
    displayed = []
    monkeypatch.setattr(message_module, "display", displayed.append)
    msg = message_module.Message(payload, unsafe_allow_html=True)
    assert isinstance(displayed[-1], IPythonMarkdown)
    assert displayed[-1].data == payload
    msg.unsafe_allow_html = False
    msg.set_content(markdown=payload)
    assert_safe(displayed[-1].data)
    msg.set_content(html=payload)
    assert displayed[-1].data == payload
    msg.append_html('<b>trusted</b>')
    assert displayed[-1].data.endswith('<b>trusted</b>')


def test_cached_markdown_uses_new_safety_mode_before_render(monkeypatch):
    payload = PAYLOADS[0]
    widget = MarkdownWidget(payload, unsafe_allow_html=True)
    monkeypatch.setattr(md_module.WidgetsManager, "get_widget", lambda _: widget)
    monkeypatch.setattr(md_module, "display", lambda _: None)
    result = md_module.Markdown(payload, key="security-cache", unsafe_allow_html=False)
    assert result is widget
    assert_safe(result.value)
    result = md_module.Markdown(payload, key="security-cache", unsafe_allow_html=True)
    assert 'onerror=' in result.value


def test_formatting_and_urls_survive_without_user_styles():
    source = '''# Heading

**bold** *emphasis*

- item

> quote

```python
print("<script>")
```

| a | b |
| --- | --- |
| 1 | 2 |

[link](https://example.com "Title") ![alt](/image.png)

<span style="position:fixed" id="app">text</span>
'''
    result = render_markdown(source)
    elements = Elements(result).elements
    assert {"h1", "strong", "em", "ul", "blockquote", "pre", "code", "table", "th", "td"} <= {tag for tag, _ in elements}
    assert ('a', {'href': 'https://example.com', 'title': 'Title', 'rel': 'noopener noreferrer'}) in elements
    assert ('img', {'src': '/image.png', 'alt': 'alt'}) in elements
    assert all('style' not in attrs and 'id' not in attrs for _, attrs in elements)
    assert '&lt;script&gt;' in result


def test_sanitizer_error_does_not_fall_back_to_raw_html(monkeypatch):
    module = import_module('mercury._markdown')
    def fail(*args, **kwargs):
        raise RuntimeError('sanitizer unavailable')
    monkeypatch.setattr(module.nh3, 'clean', fail)
    with pytest.raises(RuntimeError, match='sanitizer unavailable'):
        MarkdownWidget(PAYLOADS[0])
    with pytest.raises(RuntimeError, match='sanitizer unavailable'):
        message_module.Message(PAYLOADS[0])


def test_theme_preserves_quoted_attributes_and_literal_tags():
    title = '<p title="quoted"> > onerror=alert(1)'
    source = "<div><img src=x title='" + title + "'></div>"
    widget = MarkdownWidget(source)
    assert_safe(widget.value)
    image_attrs = next(attrs for tag, attrs in Elements(widget.value).elements if tag == 'img')
    assert image_attrs['title'] == title
    assert image_attrs['src'] == 'x'
    assert image_attrs['style'] == 'max-width: 100%; height: auto;'
