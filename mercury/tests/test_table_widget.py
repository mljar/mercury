import pytest
import anywidget
from traitlets import TraitError
import pandas as pd
import polars as pl
import mercury.table as m
from mercury.table import Table, TableWidget

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


def test_table_with_all_arguments(sample_pandas_df):
    w = Table(
        sample_pandas_df,
        page_size=25,
        width="80%",
        search=True,
        select_rows=True,
        show_index_col=True,
        position="inline",
    )

    assert w.page_size == 25
    assert w.width == "80%"
    assert w.search is True
    assert w.select_rows is True
    assert w.show_index_col is True


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


# ====== PANDAS ====== #
def test_pandas_table_basic_creation(sample_pandas_df):
    w = Table(sample_pandas_df)

    assert isinstance(w, TableWidget)


def test_table_pandas_multiindex_raises(sample_pandas_df):
    df = sample_pandas_df.copy()
    df.index = pd.MultiIndex.from_arrays([df["year"], df["month"]])

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
