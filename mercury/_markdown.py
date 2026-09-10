"""Render untrusted Markdown as an HTML fragment with an explicit policy."""

import markdown
import nh3


def render_markdown(text: str, *, unsafe_allow_html: bool = False) -> str:
    body = markdown.markdown(text, extensions=["fenced_code", "tables"])
    if unsafe_allow_html:
        return body
    return nh3.clean(
        body,
        tags={
            "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
            "strong", "em", "b", "i", "s", "del", "blockquote",
            "ul", "ol", "li", "pre", "code", "a", "img",
            "table", "thead", "tbody", "tr", "th", "td",
            "div", "span", "sup", "sub",
        },
        attributes={
            "a": {"href", "title"},
            "img": {"src", "alt", "title", "width", "height"},
            "ol": {"start"},
            "th": {"colspan", "rowspan"},
            "td": {"colspan", "rowspan"},
        },
        clean_content_tags={"script", "style", "svg", "math", "iframe", "object", "template"},
        url_schemes={"http", "https", "mailto"},
        strip_comments=True,
        link_rel="noopener noreferrer",
    )
