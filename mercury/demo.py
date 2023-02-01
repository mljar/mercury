import os
import tempfile
import nbformat as nbf

def create_demo_notebook(filename = "demo.ipynb"):
    nb = nbf.v4.new_notebook()
    
    nb["cells"] = [ 
        nbf.v4.new_code_cell("""# install packages needed for demo
# if you have those packages installed 
# please remove this cell to speedup notebook loading
!pip install -q pandas
!pip install -q numpy
!pip install -q matplotlib"""), 
        nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from IPython.display import Markdown as md"""),
        nbf.v4.new_code_cell("import mercury as mr"),
        nbf.v4.new_code_cell("""# control app with App class
app = mr.App(title="🚀 Mercury demo", description="Showcase of Mercury Widgets", show_code = False)"""),
        nbf.v4.new_markdown_cell("""# Mercury demo 👋

Share your notebooks with everyone thanks to Mercury framework.

We show you example how you can use Mercury Widgets."""), 
        nbf.v4.new_code_cell("""samples = mr.Slider(label="Number of samples", min=50, max=100, value=75)
features = mr.Select(label="Number of features", choices=["5", "10", "15"], value="10")"""), 
        nbf.v4.new_code_cell("""data = {}
for i in range(int(features.value)):
    data[f"Feature {i}"] = np.random.rand(samples.value)
df = pd.DataFrame(data)"""),
        nbf.v4.new_markdown_cell("## Random data 🎲"),
        nbf.v4.new_code_cell("df"),
        nbf.v4.new_markdown_cell("## Scatter plot 📈"),
        nbf.v4.new_code_cell("""_ = plt.plot(df["Feature 1"], df["Feature 2"], '*')"""),
        nbf.v4.new_markdown_cell("## Random data histogram 📊"),
        nbf.v4.new_code_cell("""_ = plt.hist(df["Feature 1"], bins=40)"""),
        nbf.v4.new_code_cell("""name = mr.Text(label="What is you name?", value="Piotr")"""),
        nbf.v4.new_code_cell('''md(f"""## Thank you {name.value} 🚀

For more examples please check our documentation at <a href="https://runmercury.com" target="_blank">RunMercury.com<a> 📚
""")'''),

    ]
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        nbf.write(nb, f)



