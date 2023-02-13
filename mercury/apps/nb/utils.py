import nbformat as nbf


def test_notebook(markdown=[], code=[]):
    nb = nbf.v4.new_notebook()
    nb["cells"] = []
    for m in markdown:
        nb["cells"] += [nbf.v4.new_markdown_cell(m)]
    for c in code:
        nb["cells"] += [nbf.v4.new_code_cell(c)]

    return nb


def one_cell_notebook(code=""):
    nb = nbf.v4.new_notebook()
    nb["cells"] = [nbf.v4.new_code_cell(code)]
    return nb
