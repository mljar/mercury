import pytest
from traitlets import TraitError

import mercury.file as file_module
from mercury.file import UploadFile, UploadedFile, UploadFileWidget
from mercury.manager import WidgetsManager
from mercury.render_context import source_cell_context


def setup_function():
    WidgetsManager.widgets.clear()


def teardown_function():
    WidgetsManager.widgets.clear()


def test_upload_file_defaults(monkeypatch):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    widget = UploadFile()

    assert widget.label == "Upload file"
    assert widget.max_file_size == "100MB"
    assert widget.multiple is False
    assert widget.accept == ""
    assert widget.position == "sidebar"
    assert widget.disabled is False
    assert widget.hidden is False
    assert widget.file_sizes == []
    assert widget.revision == 0


def test_upload_file_passes_constructor_arguments(monkeypatch):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    widget = UploadFile(
        label="Upload CSV",
        max_file_size="500kb",
        multiple=True,
        accept=".csv",
        position="inline",
        disabled=True,
        hidden=True,
    )

    assert widget.label == "Upload CSV"
    assert widget.max_file_size == "500KB"
    assert widget.multiple is True
    assert widget.accept == ".csv"
    assert widget.position == "inline"
    assert widget.disabled is True
    assert widget.hidden is True


@pytest.mark.parametrize("value, normalized", [
    ("1KB", "1KB"),
    ("10mb", "10MB"),
    ("2 GB", "2GB"),
])
def test_upload_file_accepts_valid_max_file_size(monkeypatch, value, normalized):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    widget = UploadFile(max_file_size=value)

    assert widget.max_file_size == normalized


@pytest.mark.parametrize("value", ["", "10", "MB", "0MB", "10TB", 10])
def test_upload_file_rejects_invalid_max_file_size(monkeypatch, value):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    with pytest.raises(ValueError, match="max_file_size"):
        UploadFile(max_file_size=value)


@pytest.mark.parametrize("value, normalized", [
    (".csv", ".csv"),
    (" .csv , .tsv ", ".csv,.tsv"),
    ([".csv", ".TSV"], ".csv,.tsv"),
    ("image/*", "image/*"),
])
def test_upload_file_accept_normalization(monkeypatch, value, normalized):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    widget = UploadFile(accept=value)

    assert widget.accept == normalized


@pytest.mark.parametrize("value", [123, [".csv", 2], [".csv", ""], " , "])
def test_upload_file_rejects_invalid_accept(monkeypatch, value):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    with pytest.raises(ValueError, match="accept"):
        UploadFile(accept=value)


def test_upload_file_accessors_return_first_file_and_all_files():
    widget = UploadFileWidget()
    widget.values = [[65, 66], [67]]
    widget.filenames = ["a.txt", "b.txt"]

    assert widget.name == "a.txt"
    assert widget.value == b"AB"
    assert widget.names == ["a.txt", "b.txt"]
    assert widget.values_bytes == [b"AB", b"C"]
    assert [file.name for file in widget.files] == ["a.txt", "b.txt"]
    assert [file.value for file in widget] == [b"AB", b"C"]
    assert all(isinstance(file, UploadedFile) for file in widget.files)


def test_upload_file_custom_upload_message_stores_file_contents():
    widget = UploadFileWidget()

    widget._handle_file_message(
        widget,
        {
            "event": "upload_files",
            "uploaded_filenames": ["a.txt", "b.txt"],
            "uploaded_file_types": ["text/plain", "text/plain"],
            "replace": True,
            "revision": 1,
        },
        [b"AB", b"C"],
    )
    widget.filenames = ["a.txt", "b.txt"]

    assert widget.values_bytes == [b"AB", b"C"]
    assert widget.values == [[65, 66], [67]]


def test_upload_file_custom_remove_message_updates_runtime_store():
    widget = UploadFileWidget()
    widget.values = [[65, 66], [67]]
    widget.filenames = ["a.txt", "b.txt"]

    widget._handle_file_message(
        widget,
        {
            "event": "remove_file",
            "index": 0,
            "revision": 2,
        },
        [],
    )
    widget.filenames = ["b.txt"]

    assert widget.values_bytes == [b"C"]
    assert widget.name == "b.txt"
    assert widget.value == b"C"


def test_upload_file_appends_runtime_store_for_multiple_operations():
    widget = UploadFileWidget()

    widget._handle_file_message(
        widget,
        {
            "event": "upload_files",
            "uploaded_filenames": ["a.txt"],
            "uploaded_file_types": ["text/plain"],
            "replace": True,
            "revision": 1,
        },
        [b"A"],
    )
    widget._handle_file_message(
        widget,
        {
            "event": "upload_files",
            "uploaded_filenames": ["b.txt"],
            "uploaded_file_types": ["text/plain"],
            "replace": False,
            "revision": 2,
        },
        [b"B"],
    )
    widget.filenames = ["a.txt", "b.txt"]

    assert widget.values_bytes == [b"A", b"B"]
    assert [file.name for file in widget.files] == ["a.txt", "b.txt"]


def test_upload_file_ignores_stale_operation_revision():
    widget = UploadFileWidget()

    widget._handle_file_message(
        widget,
        {
            "event": "upload_files",
            "uploaded_filenames": ["a.txt"],
            "uploaded_file_types": ["text/plain"],
            "replace": True,
            "revision": 2,
        },
        [b"A"],
    )
    widget._handle_file_message(
        widget,
        {
            "event": "remove_file",
            "index": 0,
            "revision": 1,
        },
        [],
    )
    widget.filenames = ["a.txt"]

    assert widget.values_bytes == [b"A"]


def test_upload_file_replacement_with_same_filename_updates_runtime_contents():
    widget = UploadFileWidget()

    widget._handle_file_message(
        widget,
        {
            "event": "upload_files",
            "uploaded_filenames": ["data.csv"],
            "uploaded_file_types": ["text/csv"],
            "replace": True,
            "revision": 1,
        },
        [b"old"],
    )
    widget.filenames = ["data.csv"]
    widget.file_sizes = [3]
    widget.revision = 1

    widget._handle_file_message(
        widget,
        {
            "event": "upload_files",
            "uploaded_filenames": ["data.csv"],
            "uploaded_file_types": ["text/csv"],
            "replace": True,
            "revision": 2,
        },
        [b"new-content"],
    )
    widget.filenames = ["data.csv"]
    widget.file_sizes = [11]
    widget.revision = 2

    assert widget.name == "data.csv"
    assert widget.value == b"new-content"
    assert widget.values_bytes == [b"new-content"]


def test_upload_file_accept_rejects_disallowed_runtime_upload():
    widget = UploadFileWidget(accept=".csv")

    with pytest.raises(ValueError, match="not allowed"):
        widget._handle_file_message(
            widget,
            {
                "event": "upload_files",
                "uploaded_filenames": ["image.png"],
                "uploaded_file_types": ["image/png"],
                "replace": True,
                "revision": 1,
            },
            [b"png-bytes"],
        )


def test_upload_file_accept_allows_extension_match():
    widget = UploadFileWidget(accept=".csv,.tsv")

    widget._handle_file_message(
        widget,
        {
            "event": "upload_files",
            "uploaded_filenames": ["data.csv"],
            "uploaded_file_types": [""],
            "replace": True,
            "revision": 1,
        },
        [b"csv-bytes"],
    )
    widget.filenames = ["data.csv"]

    assert widget.value == b"csv-bytes"


def test_upload_file_invalid_position_raises_traiterror():
    widget = UploadFileWidget()

    with pytest.raises(TraitError):
        widget.position = "top"


def test_upload_file_repr_mimebundle_adds_mercury_metadata(monkeypatch):
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0]), dict(base_result[1])]

    monkeypatch.setattr(
        file_module.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr
    )

    widget = UploadFileWidget(position="inline")
    data = widget._repr_mimebundle_()

    assert len(data) == 2
    assert file_module.MERCURY_MIMETYPE in data[0]
    metadata = data[0][file_module.MERCURY_MIMETYPE]
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]
    assert "text/plain" not in data[0]


def test_upload_file_repr_mimebundle_not_modified_when_single_mimetype(monkeypatch):
    base_result = [{"text/plain": "foo"}]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0])]

    monkeypatch.setattr(
        file_module.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr
    )

    widget = UploadFileWidget()
    data = widget._repr_mimebundle_()

    assert data == base_result


def test_upload_file_gets_source_cell_metadata(monkeypatch):
    monkeypatch.setattr(file_module, "display", lambda *_: None)
    WidgetsManager.clear()

    with source_cell_context("cell-upload"):
        widget = UploadFile(label="Upload CSV")

    assert widget.source_cell_id == "cell-upload"
    assert widget.cell_id == "cell-upload"
    assert widget.render_slot_id is None
    assert widget.layout_path is None


def test_upload_file_cached_widget_updates_render_metadata(monkeypatch):
    monkeypatch.setattr(file_module, "display", lambda *_: None)
    WidgetsManager.clear()

    with source_cell_context("cell-one"):
        widget = UploadFile(label="Upload CSV")

    assert widget.source_cell_id == "cell-one"

    with source_cell_context("cell-two"):
        cached = UploadFile(label="Upload CSV")

    assert cached is widget
    assert cached.source_cell_id == "cell-two"
    assert cached.cell_id == "cell-two"
