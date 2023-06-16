

<p align="center">
  <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/main.png#gh-light-mode-only" width="100%" />  
</p>
<p align="center">
  <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/main_black.png#gh-dark-mode-only" width="100%" />  
</p>

[![Tests](https://github.com/mljar/mercury/actions/workflows/run-tests.yml/badge.svg)](https://github.com/mljar/mercury/actions/workflows/run-tests.yml)
[![PyPI version](https://badge.fury.io/py/mercury.svg)](https://badge.fury.io/py/mercury)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/mercury.svg)](https://pypi.python.org/pypi/mercury/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/mljar-mercury/badges/license.svg)](https://anaconda.org/conda-forge/mljar-mercury)

# Build Web Apps in Jupyter Notebook

Mercury allows you to add interactive widgets in Python notebooks, so you can share notebooks as web applications. Forget about rewriting notebooks to web frameworks just to share your results. Mercury offers a set of widgets with simple re-execution of cells.

You can build with Mercury:
- Turn your notebook into beautiful [Web Apps](https://runmercury.com/tutorials/web-app-python-jupyter-notebook/),
- Create interactive [Presentations](https://runmercury.com/tutorials/presentation-python-jupyter-notebook/) with widgets, you can recompute slides during the show,
- Share notebooks as static [Websites](https://runmercury.com/tutorials/website-python-jupyter-notebook/),

- Build data-rich [Dashboards](https://runmercury.com/tutorials/dashboard-python-jupyter-notebook/) with widgets,
- Create [Reports](https://runmercury.com/tutorials/report-python-jupyter-notebook/) with PDF exports, automatic scheduling, and email notifications (coming soon),
- Serve Python notebooks as [REST API](https://runmercury.com/tutorials/rest-api-python-jupyter-notebook/) endpoints (coming soon).

 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/What_to_build.png#gh-light-mode-only" width="100%" />  
</p>
 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/What_to_build_black.png#gh-dark-mode-only" width="100%" />  
</p>

Mercury features:
- add widgets with Python code - no frontend experience needed!
- hide or show the notebook's code,
- export executed notebook to PDF or HTML,
- share multiple notebooks - no limits!
- embed notebook on any website,
- easy file upload and download from the notebook,
- add authentication to notebooks (coming soon),
- schedule automatic notebook execution (coming soon).

## Widgets

Mercury provides multiple widgets. There are 3 types of widgets:
- [Input widgets](https://runmercury.com/docs/input-widgets/) are components that will appear in the sidebar when running the notebook in Mercury. They can be used to provide user input or trigger action in the notebook.
- [Output widgets](https://runmercury.com/docs/output-widgets/) help present notebook results to the user and control execution flow.
- [Custom Widgets](https://runmercury.com/docs/custom-widgets/) - you can use many custom widgets, for example, PyDeck, and Pivot Tables.
 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/widgets3.png#gh-light-mode-only" width="100%" />  
</p>
 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/widgets_black.png#gh-dark-mode-only" width="100%" />  
</p>
## Integrations
 
Mercury works with virtually every Python package!
Among the most important are machine learning libraries such as Scikit-Learn, Pandas, and Seaborn or visualization libraries: Plotly, matplotlib, Vega-Altair, and Ipyvizzu.
 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/Integrations.png#gh-light-mode-only" width="100%" />  
</p>
 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/Integrations_black.png#gh-dark-mode-only" width="100%" />  
</p>

## Example

Simple code example that creates a widget and displays its value. You can interact with a widget in the Jupyter Notebook. Its value will be updated. However, to see the update in other cells you need to **manually execute** them.

Import package:
```python
import mercury as mr
```

Create a [`Text`](https://runmercury.com/docs/input-widgets/text/) widget:
```python
name = mr.Text(value="Piotr", label="What is your name?")
```

Print widget value:
```python
print(f"Hello {name.value}")
```

#### Code in Jupyter Notebook

<p align="center">
<kbd>
<img 
    alt="Web App from Notebook"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/hello-world-notebook-ola.png"  />  
</kbd>
</p>

#### Mercury App

Use Mercury to run notebook as web application. **Cells are automatically re-executed** after widget change. Mercury re-executes only cells with widget definition and below it. In the example, cells 2 and 3 are re-executed after widget update. 

<p align="center">
<kbd>
<img 
    alt="Web App from Notebook"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/hello-world-app-ola.gif"  />  
   </kbd>
</p>


## Documentation

📚 Read more about Mercury on [RunMercury.com](https://RunMercury.com).

## Installation

*Compatible with Python 3.7 and higher.*

Install with `pip`:

```
pip install mercury
```

Install with `conda`:

```
conda install -c conda-forge mercury
```


## Demo

Run Mercury with demo notebooks.

```
mercury run demo
```

Please check [127.0.0.1:8000](http://127.0.0.1:8000) to see demo notebooks.

## Deployment

You have several options to deploy the notebook. You can use the self-hosted option where you use [docker-compose](https://runmercury.com/docs/docker-compose/) on a VPS machine or use ngrok. There's also a possibility to use [Hugging Face Spaces](https://runmercury.com/docs/hugging-face/).

 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/jupyter-notebook-hugging-face.gif" width="100%" />  
</p>

Another option is a Self-hosted commercial where you get access to the deployment dashboard where you manage notebooks and user access. In addition, you have access to user analytics; you can freely customize the style of your application. You benefit from private forks and email support.

The third option is to use [Mercury Cloud](https://runmercury.com/docs/cloud/). It's the easiest way to share notebooks online. You will be able to create a website with a few clicks.
 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/Deployment.png#gh-light-mode-only" width="100%" />  
</p>
 <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/readme/Deployment_black.png#gh-dark-mode-only" width="100%" />  
</p>


## Mercury with your notebooks

To run Mercury with your notebook, please execute the following:

```
mercury run
```

The command should be run in the same directory as notebooks. You can change code in Jupyter Notebook, and Mercury will **instantly** update web app.



## Mercury License

Mercury is released with AGPL v3 license.

Looking for dedicated support, a commercial-friendly license, and more features? The Mercury Pro is for you. Please see the details at [our website](https://runmercury.com/pricing/).


