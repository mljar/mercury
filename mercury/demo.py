import sys
import os
import tempfile
import nbformat as nbf

def info(package):
    print("To run demo you need to have: pandas, numpy and matplotlib packages")
    print()
    print(f"Cant import {package} package")
    print(f"Please install {package} with command:")
    print()
    print(f"pip install {package}")
    print()
    sys.exit(1)

def check_needed_packages():
    try:
        import pandas
    except Exception as e:
        info("pandas")
    try:
        import numpy
    except Exception as e:
        info("numpy")
    try:
        import matplotlib
    except Exception as e:
        info("matplotlib")


def create_simple_demo_notebook(filename="demo.ipynb"):
    nb = nbf.v4.new_notebook()

    nb["cells"] = [
        nbf.v4.new_code_cell("""import mercury as mr
app = mr.App(title="Hello demo 👋", description="Hello demo with Text widget", show_code=True)
"""),
        nbf.v4.new_markdown_cell(
            """# Mercury demo 👋

Share your notebooks with everyone thanks to Mercury framework!

Please write your name in the left side bar and press **Enter** ⌨️ 

The notebook will be automatically recomputed. Only cells with widget definition and below are recomputed. That's why it is fast!

You can download executed notebook as HTML or PDF (just click in the left side bar).

You can edit this notebook in the Jupyter Notebook, and changes will appear instantly in the Mercury.
"""
        ),
        nbf.v4.new_code_cell(
            """name = mr.Text(label="What is you name?", value="Piotr")"""
        ),
        nbf.v4.new_code_cell(
            '''mr.Markdown(f"""## Hello {name.value}! 

For more examples please check our documentation at <a href="https://runmercury.com" target="_blank">RunMercury.com<a> 📚
""")'''
        ),
    ]
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)


def create_demo_notebook(filename="demo-dataframe-and-plots.ipynb"):
    nb = nbf.v4.new_notebook()

    nb["cells"] = [
        nbf.v4.new_code_cell(
            """import pandas as pd
import numpy as np
from matplotlib import pyplot as plt"""
        ),
        nbf.v4.new_code_cell("import mercury as mr"),
        nbf.v4.new_code_cell(
            """# control app with App class
app = mr.App(title="DataFrame & Plots 🚀", description="Showcase of Mercury Widgets", show_code = False)"""
        ),
        nbf.v4.new_markdown_cell(
            """# DataFrame and Plots 🎲📊

Share your notebooks with everyone thanks to Mercury framework.

Please change number of samples and number of features in the left side bar. Notebook will be recomputed after widget change."""
        ),
        nbf.v4.new_code_cell(
            """samples = mr.Slider(label="Number of samples", min=50, max=100, value=75)
features = mr.Select(label="Number of features", choices=["5", "10", "15"], value="10")"""
        ),
        nbf.v4.new_code_cell(
            """data = {}
for i in range(int(features.value)):
    data[f"Feature {i}"] = np.random.rand(samples.value)
df = pd.DataFrame(data)"""
        ),
        nbf.v4.new_markdown_cell("## Random data 🎲"),
        nbf.v4.new_code_cell("df"),
        nbf.v4.new_markdown_cell("## Scatter plot 📈"),
        nbf.v4.new_code_cell("""_ = plt.plot(df["Feature 1"], df["Feature 2"], '*')"""),
        nbf.v4.new_markdown_cell("## Random data histogram 📊"),
        nbf.v4.new_code_cell("""_ = plt.hist(df["Feature 1"], bins=40)"""),
    ]
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)


def create_slides_demo_notebook(filename="demo-slides.ipynb"):
    nb = nbf.v4.new_notebook()

    nb["cells"] = [
        nbf.v4.new_code_cell(
            """import mercury as mr
import numpy as np
from matplotlib import pyplot as plt

app = mr.App(title="Slides demo 📝", description="Wouldn't it be amazing to recompute slides during the show?") """,
            metadata={"slideshow": {"slide_type": "skip"}},
        ),
        nbf.v4.new_markdown_cell(
            """# Interactive presentation 📝""",
            metadata={"slideshow": {"slide_type": "slide"}},
        ),
        nbf.v4.new_markdown_cell(
            """## Recompute slides 🖥️

- You can create interactive presentation with Mercury
- Users can recompute slides by changing widgets
- You can enter full screen by pressing **F** and exit with **Esc**
- Please check next slides ➡️

""",
            metadata={"slideshow": {"slide_type": "slide"}},
        ),
        nbf.v4.new_code_cell(
            """name = mr.Text(label="What is your name?", value="Piotr")""",
            metadata={"slideshow": {"slide_type": "skip"}},
        ),
        nbf.v4.new_code_cell(
            '''mr.Markdown(f"""## Hello {name.value}!

{name.value}, this slide is recomputed after name change in the left side bar.

Please change the name value in the left side bar and press **Enter**.

Please check next slide ➡️

""")''',
            metadata={"slideshow": {"slide_type": "slide"}},
        ),
        nbf.v4.new_code_cell(
            """samples = mr.Slider(label="How many samples", value=75, min=50, max=100)
color = mr.Select(label="Mark color", value="blue", choices=["blue", "green", "red"])
""",
            metadata={"slideshow": {"slide_type": "skip"}},
        ),
        nbf.v4.new_code_cell(
            '''mr.Markdown("""## Scatter plot 🎲
Please change number of samples and mark color in the left side bar. The plot will be updated during the slide show.""")
_ = plt.plot(np.random.rand(samples.value), np.random.rand(samples.value), "*", color=color.value)''',
            metadata={"slideshow": {"slide_type": "slide"}},
        ),
        nbf.v4.new_markdown_cell("""## Thank you!
        
Please check our documentation at <a href="https://runmercury.com" target="_blank">RunMercury.com</a> for more information 📚

""", metadata={"slideshow": {"slide_type": "slide"}})
    ]
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)


def create_welcome(filename="welcome.md"):
    content = """
# Welcome in Mercury 👋

Mercury framework allows you easily turn Jupyter Notebooks into shareble web applications.

You can create beautiful and interactive web applications, reports, dashboards and presentations.

Mercury features:
- add widgets with simple Python API, 
- simple cell execution model - widgets trigger cell execution below the widget definition,
- hide or show notebook code,
- share multiple notebooks,
- executed notebook can be exported to HTML or PDF,
- embed notebook apps on any website,
- easily deploy (free & public Mercury cloud comming soon!)
- easily add authentication to notebooks (comming soon!)
- schedule automatic execution (comming soon!)

Please check our documentation at <a href="https://runmercury.com" target="_blank">RunMercury.com</a> for more information 📚

This text can be edited by changing `welcome.md` file. Demo notebooks can be edited in Jupyter. 

All files created for demo are in the current directory.

## Demo applications

    """
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        f.write(content)
