import uuid
import json
import ipywidgets as widgets
from IPython.display import display, clear_output
from .message import Message, MSG_CSS_CLASS



class Chat:
    def __init__(self, placeholder="💬 No messages yet. Start the conversation!"):
        """
        scroll_container_selector: Optional CSS selector of your app's scrollable container.
        Example: ".mljar-app-main" or "#right-pane".
        If None, we auto-detect the nearest scrollable ancestor.
        """
        self.messages = []
        self.scroll_container_selector = "#mercury-main-panel, .mercury-main-panel"

        self.placeholder_label = widgets.HTML(
            '''
            <div style="
              color:#b5b5b5;
              text-align:center;
              padding:40px 0;
              font-size:1.1em;
              background:#fff;
            ">
              💬 No messages yet. Start the conversation!
            </div>
            '''
            if placeholder is None else
            f'''
            <div style="
              color:#b5b5b5;
              text-align:center;
              padding:40px 0;
              font-size:1.1em;
              background:#fff;
            ">{placeholder}</div>
            '''
        )

        # unique class to target this chat only
        self._dom_class = "mljar-chat-" + uuid.uuid4().hex[:8]

        self.vbox = widgets.VBox(
            [self.placeholder_label],
            layout=widgets.Layout(
                width="100%",
                padding="4px",
                background_color="#fff",
                overflow_y="visible",  # no internal scrollbar; page/app scrolls
            ),
        )
        self.vbox.add_class(self._dom_class)

        # tiny Output used to run JS reliably after each render
        self._js = widgets.Output()
        clear_output(wait=True)
        display(self.vbox, self._js)

    def _render(self):
        import json
        from IPython.display import Javascript, display

        self.vbox.children = self.messages or [self.placeholder_label]

        chat_class_json = json.dumps(self._dom_class)
        selector = self.scroll_container_selector or "#mercury-main-panel, .mercury-main-panel"
        preferred_selector_json = json.dumps(selector)

        js = "\n".join([
            "(function(){",
            "  function isScrollable(el){",
            "    if(!el) return false;",
            "    const cs = getComputedStyle(el);",
            "    const oy = cs.overflowY, o = cs.overflow;",
            "    const can = el.scrollHeight > (el.clientHeight + 2);",
            "    return can && (oy==='auto'||oy==='scroll'||o==='auto'||o==='scroll');",
            "  }",
            "  function findScrollableWithin(root){",
            "    if(!root) return null;",
            "    if(isScrollable(root)) return root;",
            "    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null);",
            "    let n = walker.currentNode;",
            "    while((n = walker.nextNode())){ if(isScrollable(n)) return n; }",
            "    return null;",
            "  }",
            "  function getScrollableAncestor(node){",
            "    let cur = node && node.parentElement;",
            "    while(cur){ if(isScrollable(cur)) return cur; cur = cur.parentElement; }",
            "    return null;",
            "  }",
            "  function scrollIntoContainer(el, container){",
            "    if(!el||!container) return;",
            "    let y = 0, n = el;",
            "    while(n && n !== container){ y += n.offsetTop || 0; n = n.offsetParent; }",
            "    const target = Math.max(0, y - (container.clientHeight - el.clientHeight) + 16);",
            "    container.scrollTop = target;",
            "  }",
            "  function scrollPageFallback(el){",
            "    try { el.scrollIntoView({behavior:'smooth', block:'end'}); } catch(e) {}",
            "  }",
            "",
            "  const chats = document.getElementsByClassName(" + chat_class_json + ");",
            "  if(!chats || !chats.length) return;",
            "  const chat = chats[0];",
            "  const msgs = chat.getElementsByClassName('" + MSG_CSS_CLASS + "');",
            "  if(!msgs || !msgs.length) return;",
            "  const last = msgs[msgs.length - 1];",
            "",
            "  function tick(){",
            "    const pref = document.querySelector(" + preferred_selector_json + ");",
            "    const scroller = findScrollableWithin(pref) || getScrollableAncestor(last) || document.scrollingElement;",
            "    if(scroller) scrollIntoContainer(last, scroller);",
            "    else scrollPageFallback(last);",
            "  }",
            "",
            "  // Give big outputs (plots) a moment to layout",
            "  requestAnimationFrame(()=>setTimeout(tick, 100));",
            "})();",
        ])

        with self._js:
            self._js.clear_output(wait=True)
            display(Javascript(js))


    def add(self, message: Message):
        self.messages.append(message)
        self._render()

    def clear(self):
        self.messages.clear()
        self._render()

