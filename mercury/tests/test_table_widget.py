import pytest
from traitlets import TraitError
import pandas as pd
import polars as pl
import mercury.table as m
from mercury.manager import WidgetsManager
from mercury.table import Table, TableWidget


def setup_function():
    WidgetsManager.widgets.clear()


def teardown_function():
    WidgetsManager.widgets.clear()


# ====== EXAMPLE DATA ====== #

@pytest.fixture
def sample_pandas_df():
    return pd.DataFrame(
        {
            "month": [1, 4, 7, 10] * 20,
            "year": [2012, 2014, 2013, 2014] * 20,
            "sale": [55, 40, 84, 31] * 20,
            "text": ["a", "b", "c", "d"] * 20,
            "category": ["X", "Y", "Z", "W"] * 20,
        }
    )


@pytest.fixture
def sample_polars_df():
    return pl.DataFrame(
        {
            "text": ["a", "b", "a", "c"],
            "value": [1, 2, 3, 4],
        }
    )


@pytest.fixture
def sample_dicts_data():
    return [
        {"text": "a", "value": 1},
        {"text": "b", "value": 2},
        {"text": "a", "value": 3},
    ]


# ====== GENERAL ====== #


def test_table_defaults(sample_pandas_df):
    w = Table(sample_pandas_df)

    assert w.page_size == 50
    assert w.search is False
    assert w.select_rows is False
    assert w.show_index_col is False
    assert w.width == "100%"
    assert w.height is None


def test_table_with_all_arguments(sample_pandas_df):
    w = Table(
        sample_pandas_df,
        page_size=25,
        width="80%",
        height="360px",
        search=True,
        select_rows=True,
        show_index_col=True,
        position="inline",
    )

    assert w.page_size == 25
    assert w.width == "80%"
    assert w.height == "360px"
    assert w.search is True
    assert w.select_rows is True
    assert w.show_index_col is True


def test_table_reuses_cached_widget_for_same_data(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)

    first = Table([{"name": "Alice", "score": 10}])
    second = Table([{"name": "Alice", "score": 10}])

    assert second is first
    assert len(WidgetsManager.widgets) == 1


def test_table_data_hash_separates_different_data(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)

    first = Table([{"name": "Alice", "score": 10}])
    second = Table([{"name": "Alice", "score": 11}])

    assert second is not first
    assert len(WidgetsManager.widgets) == 2


def test_table_key_disambiguates_same_data(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)

    first = Table([{"name": "Alice", "score": 10}], key="first")
    second = Table([{"name": "Alice", "score": 10}], key="second")

    assert second is not first
    assert len(WidgetsManager.widgets) == 2


def test_table_height_is_part_of_cache_key(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)

    first = Table([{"name": "Alice", "score": 10}])
    second = Table([{"name": "Alice", "score": 10}], height="300px")

    assert second is not first
    assert len(WidgetsManager.widgets) == 2


def test_table_displays_by_default(monkeypatch):
    displayed = []
    monkeypatch.setattr(m, "display", lambda widget: displayed.append(widget))

    widget = Table([{"name": "Alice", "score": 10}])

    assert displayed == [widget]


def test_table_display_now_false_does_not_display(monkeypatch):
    displayed = []
    monkeypatch.setattr(m, "display", lambda widget: displayed.append(widget))

    widget = Table([{"name": "Alice", "score": 10}], display_now=False)

    assert isinstance(widget, TableWidget)
    assert displayed == []


def test_table_display_now_is_not_part_of_cache_key(monkeypatch):
    displayed = []
    monkeypatch.setattr(m, "display", lambda widget: displayed.append(widget))

    first = Table([{"name": "Alice", "score": 10}], display_now=False)
    second = Table([{"name": "Alice", "score": 10}], display_now=True)

    assert second is first
    assert displayed == [first]
    assert len(WidgetsManager.widgets) == 1


def test_cached_table_respects_display_now_false(monkeypatch):
    displayed = []
    monkeypatch.setattr(m, "display", lambda widget: displayed.append(widget))

    first = Table([{"name": "Alice", "score": 10}])
    second = Table([{"name": "Alice", "score": 10}], display_now=False)

    assert second is first
    assert displayed == [first]
    assert len(WidgetsManager.widgets) == 1


def test_table_hashes_dataframe_content(monkeypatch):
    monkeypatch.setattr(m, "display", lambda *_: None)

    first = Table(pd.DataFrame({"name": ["Alice"], "score": [10]}))
    second = Table(pd.DataFrame({"name": ["Alice"], "score": [10]}))
    third = Table(pd.DataFrame({"name": ["Alice"], "score": [11]}))

    assert second is first
    assert third is not first
    assert len(WidgetsManager.widgets) == 2


def test_table_invalid_page_size_string_raises(sample_pandas_df):
    with pytest.raises(Exception, match="page_size"):
        Table(sample_pandas_df, page_size="abc")


def test_table_invalid_page_size_none_raises(sample_pandas_df):
    with pytest.raises(Exception, match="page_size"):
        Table(sample_pandas_df, page_size=None)


def test_table_invalid_width_string_raises(sample_pandas_df):
    with pytest.raises(ValueError, match="width"):
        Table(sample_pandas_df, width="wide")


def test_table_invalid_width_number_raises(sample_pandas_df):
    with pytest.raises(ValueError, match="width"):
        Table(sample_pandas_df, width=400)


def test_table_invalid_height_string_raises(sample_pandas_df):
    with pytest.raises(ValueError, match="height"):
        Table(sample_pandas_df, height="tall")


def test_table_invalid_height_number_raises(sample_pandas_df):
    with pytest.raises(ValueError, match="height"):
        Table(sample_pandas_df, height=400)


def test_table_zero_page_size_clamps_to_first_page(sample_pandas_df):
    w = Table(sample_pandas_df, page_size=0)

    assert len(w.data) == 1
    assert w.table_page == 1
    assert w._filtered_length == len(sample_pandas_df)


def test_table_negative_page_size_clamps_to_first_page(sample_pandas_df):
    w = Table(sample_pandas_df, page_size=-5)

    assert len(w.data) == 1
    assert w.table_page == 1
    assert w._filtered_length == len(sample_pandas_df)


# ====== PANDAS ====== #
def test_pandas_table_basic_creation(sample_pandas_df):
    w = Table(sample_pandas_df)

    assert isinstance(w, TableWidget)


def test_table_pandas_multiindex_raises(sample_pandas_df):
    df = sample_pandas_df.copy()
    df.index = pd.MultiIndex.from_arrays([df["year"], df["month"]])

    with pytest.raises(TraitError):
        Table(df)


def test_table_pandas_multiindex_columns_raises(sample_pandas_df):
    df = sample_pandas_df.copy()
    df.columns = pd.MultiIndex.from_tuples(
        [("date", "month"), ("date", "year"), ("metric", "sale"), ("meta", "text"), ("meta", "category")]
    )

    with pytest.raises(TraitError):
        Table(df)


def test_pandas_filtering_row_count(sample_pandas_df):
    w = Table(sample_pandas_df)

    w.table_search_query = "2014"

    assert w._filtered_length == 40


def test_pandas_filtering_row_value(sample_pandas_df):
    w = Table(sample_pandas_df)

    w.table_search_query = "c"

    filtered = w._filtered_df

    assert filtered is not None
    assert not filtered.empty
    assert (filtered["text"] == "c").all()


def test_pandas_sorting_ascending(sample_pandas_df):
    w = Table(sample_pandas_df)

    w.table_sort_column = "sale"
    w.table_sort_direction = 1

    sorted_df = w._sorted_df

    assert sorted_df is not None
    assert sorted_df.iloc[0]["sale"] == 31
    assert sorted_df.iloc[-1]["sale"] == 84


def test_pandas_sorting_descending(sample_pandas_df):
    w = Table(sample_pandas_df)

    w.table_sort_column = "sale"
    w.table_sort_direction = 2

    sorted_df = w._sorted_df

    assert sorted_df is not None
    assert sorted_df.iloc[0]["sale"] == 84
    assert sorted_df.iloc[-1]["sale"] == 31


# ====== POLARS ====== #
def test_polars_table_basic_creation(sample_polars_df):
    w = Table(sample_polars_df)

    assert isinstance(w, TableWidget)


def test_polars_filtering_row_count(sample_polars_df):
    w = Table(sample_polars_df)

    w.table_search_query = "a"

    assert w._filtered_length == 2


def test_polars_filtering_row_value(sample_polars_df):
    w = Table(sample_polars_df)

    w.table_search_query = "a"

    filtered = w._filtered_df

    assert filtered is not None
    assert filtered.height == 2
    assert filtered["text"].to_list() == ["a", "a"]


def test_polars_sorting_ascending(sample_polars_df):
    w = Table(sample_polars_df)

    w.table_sort_column = "value"
    w.table_sort_direction = 1

    sorted_df = w._sorted_df

    assert sorted_df["value"].to_list() == [1, 2, 3, 4]


def test_polars_sorting_descending(sample_polars_df):
    w = Table(sample_polars_df)

    w.table_sort_column = "value"
    w.table_sort_direction = 2

    sorted_df = w._sorted_df

    assert sorted_df["value"].to_list() == [4, 3, 2, 1]


# ====== DICTS ====== #
def test_dicts_table_basic_creation(sample_dicts_data):
    w = Table(sample_dicts_data)


def test_dicts_filtering_row_count(sample_dicts_data):
    w = Table(sample_dicts_data)

    w.table_search_query = "a"

    assert w._filtered_length == 2


def test_dicts_filtering_row_value(sample_dicts_data):
    w = Table(sample_dicts_data)

    w.table_search_query = "a"

    filtered = w._filtered_data

    assert filtered is not None
    assert len(filtered) == 2
    assert all(row["text"] == "a" for row in filtered)


def test_dicts_sorting_ascending(sample_dicts_data):
    w = Table(sample_dicts_data)

    w.table_sort_column = "value"
    w.table_sort_direction = 1

    sorted_data = w._sorted_data

    assert [row["value"] for row in sorted_data] == [1, 2, 3]


def test_dicts_sorting_descending(sample_dicts_data):
    w = Table(sample_dicts_data)

    w.table_sort_column = "value"
    w.table_sort_direction = 2

    sorted_data = w._sorted_data

    assert [row["value"] for row in sorted_data] == [3, 2, 1]
