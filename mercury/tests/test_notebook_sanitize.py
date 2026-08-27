from mercury_app.notebook_sanitize import sanitize_notebook_for_mercury_runtime


def test_sanitize_notebook_removes_runtime_artifacts_and_preserves_app_source():
    notebook = {
        "metadata": {
            "kernelspec": {"name": "python3"},
            "language_info": {"name": "python"},
            "mercury": {"title": "Echo Chat", "autoRerun": True},
            "widgets": {
                "application/vnd.jupyter.widget-state+json": {
                    "state": {
                        "abc": {
                            "state": {
                                "_esm": "export default {}",
                                "_css": ".x{}",
                            }
                        }
                    }
                }
            },
        },
        "cells": [
            {
                "cell_type": "code",
                "id": "code-1",
                "source": "import mercury as mr",
                "execution_count": 7,
                "outputs": [
                    {
                        "output_type": "display_data",
                        "data": {
                            "application/mercury+json": {
                                "model_id": "abc",
                                "position": "bottom",
                            },
                            "application/vnd.jupyter.widget-view+json": {
                                "model_id": "abc"
                            },
                        },
                    }
                ],
            },
            {
                "cell_type": "markdown",
                "id": "markdown-1",
                "source": "# App",
            },
        ],
    }

    sanitized = sanitize_notebook_for_mercury_runtime(notebook)

    assert "widgets" not in sanitized["metadata"]
    assert sanitized["metadata"]["mercury"] == {"title": "Echo Chat", "autoRerun": True}
    assert sanitized["metadata"]["kernelspec"] == {"name": "python3"}
    assert sanitized["metadata"]["language_info"] == {"name": "python"}

    code_cell = sanitized["cells"][0]
    assert code_cell["id"] == "code-1"
    assert code_cell["source"] == "import mercury as mr"
    assert code_cell["outputs"] == []
    assert code_cell["execution_count"] is None

    assert sanitized["cells"][1] == {
        "cell_type": "markdown",
        "id": "markdown-1",
        "source": "# App",
    }

    assert "widgets" in notebook["metadata"]
    assert notebook["cells"][0]["outputs"]


def test_sanitize_notebook_assigns_stable_ids_to_legacy_cells():
    notebook = {
        "cells": [
            {"cell_type": "code", "source": "print('first')", "outputs": []},
            {"cell_type": "code", "source": "print('second')", "outputs": []},
        ]
    }

    first = sanitize_notebook_for_mercury_runtime(notebook)
    second = sanitize_notebook_for_mercury_runtime(notebook)
    first_ids = [cell["id"] for cell in first["cells"]]

    assert first_ids == [cell["id"] for cell in second["cells"]]
    assert len(set(first_ids)) == 2
    assert all(cell_id.startswith("mrc-") for cell_id in first_ids)
