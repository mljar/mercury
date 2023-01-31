import os
import tempfile
import nbformat as nbf

def create_demo_notebook(filename = "demo.ipynb"):
    nb = nbf.v4.new_notebook()
    
    imports = "import mercury as mr"
    text = "# 🚀 Demo notebook with greetings 👋"
    variables = '''year = mr.Slider(label="Please select the year", value=2023, min=2000, max=2050)
name = mr.Text(label="What is your name?", value="Piotr")'''
    code = '''print(f"Hello {name.value} in {year.value}!")'''
    nb["cells"] = [ 
        nbf.v4.new_code_cell(imports), 
        nbf.v4.new_markdown_cell(text), 
        nbf.v4.new_code_cell(variables), 
        nbf.v4.new_code_cell(code)
    ]
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)


