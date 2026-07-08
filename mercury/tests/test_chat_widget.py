import mercury.chat.chat as chat_module
from mercury.chat.chat import Chat
from mercury.chat.message import DEFAULT_EMOJI_BACKGROUND, Message


class FakeTimer:
    instances = []

    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback
        self.cancelled = False
        self.started = False
        self.daemon = False
        FakeTimer.instances.append(self)

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True

    def fire(self):
        if not self.cancelled:
            self.callback()


def test_chat_default_height_preserves_natural_layout(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)

    chat = Chat()

    assert chat.height == ""
    assert chat.vbox.layout.height is None
    assert chat.vbox.layout.overflow == "visible"
    assert "mljar-chat-container" in chat.vbox._dom_classes


def test_chat_height_sets_internal_scroll(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)

    chat = Chat(height="600px")

    assert chat.height == "600px"
    assert chat.vbox.layout.height == "600px"
    assert chat.vbox.layout.overflow == "auto"


def test_chat_height_accepts_viewport_units(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)

    chat = Chat(height="70vh")

    assert chat.height == "70vh"
    assert chat.vbox.layout.height == "70vh"
    assert chat.vbox.layout.overflow == "auto"


def test_message_append_after_chat_add_schedules_debounced_scroll(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)
    monkeypatch.setattr(chat_module, "Timer", FakeTimer)
    FakeTimer.instances = []

    chat = Chat(scroll_debounce=0.25)
    msg = Message(role="assistant")
    chat.add(msg)
    tick_after_add = chat._scroller.tick

    msg.append_markdown("hello")

    assert chat._scroller.tick == tick_after_add
    assert len(FakeTimer.instances) == 1
    assert FakeTimer.instances[0].interval == 0.25
    assert FakeTimer.instances[0].started is True

    FakeTimer.instances[0].fire()

    assert chat._scroller.tick == tick_after_add + 1


def test_streaming_appends_are_debounced_to_one_scroll(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)
    monkeypatch.setattr(chat_module, "Timer", FakeTimer)
    FakeTimer.instances = []

    chat = Chat(scroll_debounce=0.1)
    msg = Message(role="assistant")
    chat.add(msg)
    tick_after_add = chat._scroller.tick

    msg.append_markdown("a")
    msg.append_markdown("b")
    msg.append_markdown("c")

    assert len(FakeTimer.instances) == 3
    assert FakeTimer.instances[0].cancelled is True
    assert FakeTimer.instances[1].cancelled is True
    assert chat._scroller.tick == tick_after_add

    FakeTimer.instances[-1].fire()

    assert chat._scroller.tick == tick_after_add + 1


def test_append_text_and_html_schedule_scroll(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)
    monkeypatch.setattr(chat_module, "Timer", FakeTimer)
    FakeTimer.instances = []

    chat = Chat(scroll_debounce=0.1)
    text_msg = Message(role="assistant")
    html_msg = Message(role="assistant")
    chat.add(text_msg)
    chat.add(html_msg)

    text_msg.append_text("hello")
    html_msg.append_html("<b>hello</b>")

    assert len(FakeTimer.instances) == 2


def test_clear_detaches_message_scroll_callback(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)
    monkeypatch.setattr(chat_module, "Timer", FakeTimer)
    FakeTimer.instances = []

    chat = Chat(scroll_debounce=0.1)
    msg = Message(role="assistant")
    chat.add(msg)
    chat.clear()

    msg.append_markdown("old")

    assert FakeTimer.instances == []


def test_remove_last_detaches_message_scroll_callback(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)
    monkeypatch.setattr(chat_module, "Timer", FakeTimer)
    FakeTimer.instances = []

    chat = Chat(scroll_debounce=0.1)
    msg = Message(role="assistant")
    chat.add(msg)
    chat.remove_last()

    msg.append_markdown("old")

    assert FakeTimer.instances == []


def test_scroll_debounce_zero_scrolls_immediately(monkeypatch):
    monkeypatch.setattr(chat_module, "display", lambda *_: None)
    monkeypatch.setattr(chat_module, "clear_output", lambda *_, **__: None)
    monkeypatch.setattr(chat_module, "Timer", FakeTimer)
    FakeTimer.instances = []

    chat = Chat(scroll_debounce=0)
    msg = Message(role="assistant")
    chat.add(msg)
    tick_after_add = chat._scroller.tick

    msg.append_markdown("hello")

    assert chat._scroller.tick == tick_after_add + 1
    assert FakeTimer.instances == []


def test_message_uses_default_emoji_background():
    msg = Message(role="assistant")

    avatar_html = msg.children[0].value

    assert f"background:{DEFAULT_EMOJI_BACKGROUND};" in avatar_html


def test_message_accepts_custom_emoji_background():
    msg = Message(role="assistant", emoji_background="#123456")

    avatar_html = msg.children[0].value

    assert "background:#123456;" in avatar_html
