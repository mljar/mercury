import os
import tempfile
import nbformat as nbf

def create_demo_notebook(filename = "demo.ipynb"):
    nb = nbf.v4.new_notebook()
    yaml = '''---
title: 🚀 Demo notebook
description: Simple notebook with widgets demo
params:
    year:
        input: slider
        label: Please select the year
        min: 2000
        max: 2100
        value: 2022
    greetings:
        input: select
        label: Please select greetings
        value: Hello
        choices: [Cześć, Hello, Hi, Ciao, Salut]
    name:
        input: text
        label: What is your name?
        value: Piotr
    ---'''
    text = "# 🚀 Demo notebook with greetings 👋"
    variables = '''year = 2022
greetings = "Hello"
name = "Piotr"'''
    code = '''print(f"{greetings} {name} in {year}")'''
    nb["cells"] = [nbf.v4.new_raw_cell(yaml), 
        nbf.v4.new_markdown_cell(text), 
        nbf.v4.new_code_cell(variables), 
        nbf.v4.new_code_cell(code)
    ]
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)


