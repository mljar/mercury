
<p align="center">
  <img 
    alt="Mercury convert notebook to web app"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_convert_notebook.png" width="600px" />  
</p>

# Mercury

## Share your Python notebooks with others

Easily convert your Python notebooks into interactive web apps by adding parameters in YAML.

- Simply add YAML with description of parameters needed in the notebook. 
- Share notebook with others. 
- Allow them to execute notebook with selected parameters. 
- You can decide to show or hide your code.
- Easily deploy to the server.

### Check our demo

The demo with several example notebooks is running at [http://mercury.mljar.com](http://mercury.mljar.com). No need to register.

### Share mutliple notebooks

You can share as many notebooks as you want. In the main view of the Mercury there is gallery with notebooks. You can select any notebook by clicking `Open` button.

<p align="center">
  <a href="http://mercury.mljar.com" target="_blank">
    <img 
      alt="Mercury share multiple notebooks"
      src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_share_multiple_notebooks.png" width="90%" />
  </a>  
</p>

## Convert Notebook to web app with YAML

You need to add YAML at the beginning of the notebook to be able to run it as web application in the Mercury. The YAML configuration should be added in the notebook as **Raw** cell. It should start and end with a line containing "---". Below examples how it should look like in the Jupyter Notebook and Jupyter Lab:

<p align="center" >
  <img 
    alt="Mercury Raw Cell in Jupyter Notebook"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_raw_cell_jupyter_notebook.png" width="45%" />
  <img 
    alt="Mercury Raw Cell in Jupyter Lab"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_raw_cell_jupyter_lab.png" width="45%" />
    
</p>


Allowed parameters in YAML config:

- `title` - string with a title of the notebook. It is used in the app side bar and in the gallery view.
- `author` - string with a author name (optional).
- `description` - string describing the content of the notebook. It is used in the gallery view.
- `show-code` - can be `True` or `False`. Default is set to `True`. It decides if the notebook's code will be displayed or not.
- `show-prompt` - can be `True` or `False`. Default is set to `True`. If set to `True` the prompt information will be displayed for each cell in the notebook.
- `params` - the parameters that will be used in the notebook. They will be displayed as interactive widgets in the side bar. Each parameter should have unique name that correspont to the variable name used in the code.

## Define widget with YAML

#### Widget name is a variable name
Definition of the widget (in `params`) starts with the widget name. It will correspond to the variable in the code. The name should be a valid Python variable. 

#### Widget input type
The next thing is to select the input type. It can be: `slider`, `range`, `select`, `checkbox`, `numeric`. 

#### Widget label
For each input we need to define a `label`. It will be a text displayed above (or near) the widget.

#### Widget default value
You can set a default widget by setting the `value`. The format of the `value` depends on the input type:

- for `slider` a `value` should be a number, example: `value: 5`,
- for `range` a `value` should be a list with two numbers, example `value: [3,6]`,
- for `select` with `mutli: False` a `value` should be a string, example `value: hey`,
- for `select` with `multi: True` a `value` should be a list of strings, example `value: [cześć, hi, hello]`,
- for `checkbox` a `value` should be a boolean (`True` or `False`), example: `value: True`,
- for `numeric` a `value` should be a number, example: `value: 10.2`.

The rest of parameters depends on widget input type.

#### Slider

Additional parameters:

- `min` - the minimum value for slider (default is set to 0),
- `max` - the maximum value for slider (default is set to 100).

Example YAML:

```yaml
params:
    my_variable:
        input: slider
        label: This is slider label
        value: 5
        min: 0
        max: 10
```

<p align="left" >
  <img 
    alt="Mercury Slider"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_slider.png" width="35%" />
</p>

#### Range

Additional parameters:

- `min` - the minimum value for slider (default is set to 0),
- `max` - the maximum value for slider (default is set to 100).

Example YAML:

```yaml
params:
    range_variable:
        input: range
        label: This is range label
        value: [3,6]
        min: 0
        max: 10
```
<p align="left" >
  <img 
    alt="Mercury Range"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_range.png" width="35%" />
</p>

#### Select 

Additional parameters:

- `multi` - a boolean value that decides if user can select several options (default is set to `False`).
- `choices` - a list with available choices.

Example YAML:

```yaml
params:
    select_variable:
        label: This is select label
        input: select
        value: Cześć
        choices: [Cześć, Hi, Hello]
        multi: False
```

<p align="left" >
  <img 
    alt="Mercury Select"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_select.png" width="35%" />
</p>

#### Checkbox

There are no additional parameters.

Example YAML:

```yaml
params:
    checkbox_variable:
        label: This is checkbox label
        input: checkbox
        value: True
```

<p align="left" >
  <img 
    alt="Mercury Checkbox"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_checkbox.png" width="35%" />
</p>

#### Numeric

Additional parameters:

- `min` - a minimum allowed value (default set to 0),
- `max` - a maximum allowed value (default set to 100),
- `step` - a step value (default set to 1).

```yaml
params:
    numeric_variable:
        label: This is numeric label
        input: numeric
        value: 5.5
        min: 0
        max: 10
        step: 0.1
```

<p align="left" >
  <img 
    alt="Mercury Numeric"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_numeric.png" width="35%" />
</p>

### Full example YAML

```yaml
---
title: My notebook
author: Piotr
description: My first notebook in Mercury
params:
    my_variable:
        label: This is slider label
        input: slider
        value: 5
        min: 0
        max: 10
    range_variable:
        label: This is range label
        input: range
        value: [3,6]
        min: 0
        max: 10    
    select_variable:
        label: This is select label
        input: select
        value: Cześć
        choices: [Cześć, Hi, Hello]
        multi: False
    checkbox_variable:
        label: This is checkbox label
        input: checkbox
        value: True
    numeric_variable:
        label: This is numeric label
        input: numeric
        value: 5.5
        min: 0
        max: 10
        step: 0.1
---
```

Widgets rendered from above YAML config:

<p align="left" >
  <img 
    alt="Mercury widgets"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_widgets.png" width="40%" />
</p>


### Use variables in the code

To use variables in the code simply define the variable with the same name as widget name. You can also assign the same value as defined in YAML. Please define all variables in the one cell (it can be below the cell with YAML config).

When the user will interact with widgets and click the `Run` button, the code with variables will be updated with user selected values.

Example:

<p align="left" >
  <img 
    alt="Mercury Variables"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_variables.png" width="70%" />
</p>


## Installation

You can install Mercury directly from PyPi repository with `pip` command:

```
pip install mljar-mercury
```

## Running locally

To run Mercury locally just run:

```
mercury runserver
```

This will show you Mercury website at `http://127.0.0.1:8000`. It won't display any notebooks because we didn't add any. Please stop the Mercury server for a moment (Ctrl+C).

Execute the following command to add notebook to Mercury database:

```
mercury add <path_to_notebook>
```

If you would like to add all notebooks in the directory you can use a wildcard:

```
mercury add <directory_with_notebooks>/*.ipynb
```

Please start the Mercury server to see your apps (created from notebooks).

## Notebook development

The Mercury `watch` command is perfect when you are creating a new notebook and would like to see how it will look like as web app with live changes.

Please run the following command:

```
mercury watch <path_to_your_notebook>
```

You can now open the web browser at `http://127.0.0.1:8000` and find your notebook. When you change something in the notebook code, markdown or YAML configuration and save the notebook, then it will be automatically refreshed in the web browser. You can track your changes without manual refreshing of the web app.


## Running in production

Running in production is easy. We provide several tutorials how it can be done.

- Deploy to Heroku (comming soon)
- Deploy to Digital Ocean (comming soon)
- Deploy to AWS EC2 (comming soon)
- Deploy to GCP (comming soon)
- Deploy to Azure (comming soon)

## Development

The Mercury consists of three elements:

- Frontend written in TypeScript with React+Redux
- Server written in Python with Django
- Worker written in Python with Celery

Each element needs a separate terminal during development.

### Frontend

The user interface code is in the `frontend` directory. Run all commands from there. Install dependencies:

```
yarn install
```

Run frontend:

```
yarn start
```

The frontend is served at `http://localhost:3000`.

### Server

The server code is in the `mercury` directory. Run all commands from there. Please set the virtual environment first:

```
virtualenv menv
source menv/bin/activate
pip install -r requirements.txt
```

Apply migrations:

```
python manage.py migrate
```

Run the server in development mode (`DEBUG=True`):

```
python manage.py runserver
```

The server is running at `http://127.0.0.1:8000`.

### Worker

The worker code is in the `mercury` directory (in the `apps/notebooks/tasks.py` and `apps/tasks/tasks.py` files). Please activate first the virtual environment (it is using the same virtual environment as server):

```
source menv/bin/activate
```

Run the worker:
```
celery -A server worker --loglevel=info -P gevent --concurrency 1 -E
```

## Mercury Pro

Looking for dedicated support, commercial friendly license and more features? The Mercury Pro is for you. Please see the details at [our website](https://mljar.com/pricing).


<p align="center">
  <img 
    alt="Mercury logo"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_logo_v1.png" width="30%" />
</p>
