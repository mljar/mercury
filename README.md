

<p align="center">
  <img 
    alt="Mercury convert Jupyter Notebook to Web App"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury-og.png" width="100%" />  
</p>

[![Tests](https://github.com/mljar/mercury/actions/workflows/run-tests.yml/badge.svg)](https://github.com/mljar/mercury/actions/workflows/run-tests.yml)
[![PyPI version](https://badge.fury.io/py/mercury.svg)](https://badge.fury.io/py/mercury)
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

Mercury features:
- add widgets with Python code - no frontend experience needed!
- hide or show notebook's code,
- export executed notebook to PDF or HTML,
- share muplitple notebooks - no limits!
- embed notebook on any website,
- easy file upload and download from the notebook,
- add authentication to notebooks (coming soon),
- schedule automatic notebook execution (coming soon).

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


## Demo

Run Mercury with demo notebooks.

```
mercury run demo
```

Please check [127.0.0.1:8000](http://127.0.0.1:8000) to see demo notebooks.


## Mercury with your notebooks

To run Mercury with your notebook, please execute the following:

```
mercury run
```

The command should be run in the same directory as notebooks. You can change code in Jupyter Notebook, and Mercury will **instantly** update web app.


## Mercury License

Mercury is released with AGPL v3 license.

Looking for dedicated support, a commercial-friendly license, and more features? The Mercury Pro is for you. Please see the details at [our website](https://mljar.com/pricing).


