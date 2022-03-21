<h1> Mercury Documentation </h1>

<p align="center">
  <img 
    alt="Mercury convert notebook to web app"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_convert_notebook_3.png" width="800px" />  
</p>

[![Tests](https://github.com/mljar/mercury/actions/workflows/run-tests.yml/badge.svg)](https://github.com/mljar/mercury/actions/workflows/run-tests.yml)
[![PyPI version](https://badge.fury.io/py/mljar-mercury.svg)](https://badge.fury.io/py/mljar-mercury)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/mljar-mercury/badges/installer/conda.svg)](https://conda.anaconda.org/conda-forge)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/mljar-mercury.svg)](https://pypi.python.org/pypi/mljar-mercury/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/mljar-mercury/badges/platforms.svg)](https://anaconda.org/conda-forge/mljar-mercury)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/mljar-mercury/badges/license.svg)](https://anaconda.org/conda-forge/mljar-mercury)


Mercury is a perfect tool to convert Python notebook to web app and share with non-programmers. 

- You define interactive widgets for your notebook with the YAML header. 
- Your users can change the widgets values, execute the notebook and save result (as html file).
- You can hide your code to not scare your (non-coding) collaborators.
- Easily deploy to any server.

Mercury is dual-licensed. The main features are available in the open-source version. It is perfect for quick demos, educational purposes, sharing notebooks with friends. Looking for dedicated support, a commercial-friendly license, and more features? The Mercury Pro is for you. Please see the details at our [website](https://mljar.com/pricing).

## Steps to share notebook with non-programmers

Steps to turns notebook to web app.

1. Create a notebook with your analysis.
2. Create one code cell with all your variables that will be changed by users.
3. Add the raw cell at the beginning of the notebook. 
4. Please add [YAML configuration](/yaml-parameters) there.
5. Please use the names of variables to construct widgets.
6. Check the app by running it locally.
7. Deploy to the cloud.
8. Share URL link to the server with non-technical users.