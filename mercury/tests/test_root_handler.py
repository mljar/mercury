from mercury_app.root import should_show_search_filter


def test_should_show_search_filter_only_when_more_than_three_notebooks():
    assert should_show_search_filter([], {}) is False
    assert should_show_search_filter([{}, {}], {}) is False
    assert should_show_search_filter([{}, {}, {}], {}) is False
    assert should_show_search_filter([{}, {}, {}, {}], {}) is True


def test_should_show_search_filter_respects_config_toggle():
    assert should_show_search_filter([{}, {}, {}, {}], {"show_search_filter": False}) is False
    assert should_show_search_filter([], {"show_search_filter": True}) is True
    assert should_show_search_filter([{}, {}], {"show_search_filter": True}) is True
