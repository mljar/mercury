
<p align="center">
  <img 
    alt="Mercury convert notebook to web app"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_convert_notebook_3.png" width="700px" />  
</p>

# Mercury

## Share your Python notebooks with others

Easily convert your Python notebooks into interactive web apps by adding parameters in YAML.

- Simply add YAML with a description of the parameters needed in the notebook. 
- Share a notebook with others. 
- Allow them to execute the notebook with selected parameters. 
- You can decide to show or hide your code.
- Easily deploy to the server.

Mercury is a perfect tool to share your Python notebooks with non-programmers. 
- You can turn your notebook into a web app. Sharing is as easy as sending them the URL to your server.
- You can add interactive input to your notebook by defining the YAML header. Your users can change the input and execute the notebook.
- You can hide your code to not scare your (non-coding) collaborators.
- Users can interact with notebook and save results.
- You can share a notebook as a web app with multiple users - they don't overwrite the original notebook.

## Example

#### Notebook with YAML config

The YAML config is added as the first raw cell in the notebook.

<p align="center">
  <img 
    alt="notebook with YAML config"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_greetings_3.png" width="600px" />  
</p>

#### Web Application from Notebook

The web app is generated from the notebook. Code is hidden (optional). User can change parameters, execute notebook with the `Run` button, and save results with the `Download` button.

<p align="center">
  <img 
    alt="Web App from Notebook"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_app_greetings_2.png" width="600px" />  
</p>


### Check our demo

The demo with several example notebooks is running at [http://mercury.mljar.com](http://mercury.mljar.com) (running on AWS EC2 t3a.small instance). No need to register.

The demo is running at Heroku free dyno [http://mercury-demo-1.herokuapp.com](http://mercury-demo-1.herokuapp.com) (with several notebooks-apps). No need to register. (if dyno is sleeping and notebooks are not loaded, please refresh it and wait a little)

### Share mutliple notebooks

You can share as many notebooks as you want. There is a gallery with notebooks in the home view of the Mercury. You can select any notebook by clicking the `Open` button.

<p align="center">
  <a href="http://mercury.mljar.com" target="_blank">
    <img 
      alt="Mercury share multiple notebooks"
      src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_share_multiple_notebooks.png" width="90%" />
  </a>  
</p>

## Convert Notebook to web app with YAML

You need to add YAML at the beginning of the notebook to be able to run it as a web application in the Mercury. The YAML configuration should be added as a **Raw** cell in the notebook. It should start and end with a line containing "---". Below examples of how it should look like in the Jupyter Notebook and Jupyter Lab:

<p align="center" >
  <img 
    alt="Mercury Raw Cell in Jupyter Notebook"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_raw_cell_jupyter_notebook.png" width="45%" />
  <img 
    alt="Mercury Raw Cell in Jupyter Lab"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_raw_cell_jupyter_lab.png" width="45%" />
    
</p>


Allowed parameters in YAML config:

- `title` - string with a title of the notebook. It is used in the app sidebar and the gallery view.
- `author` - string with a author name (optional).
- `description` - string describing the content of the notebook. It is used in the gallery view.
- `show-code` - can be `True` or `False`. Default is set to `True`. It decides if the notebook's code will be displayed or not.
- `show-prompt` - can be `True` or `False`. Default is set to `True`. If set to `True` prompt information will be displayed for each cell in the notebook.
- `params` - the parameters that will be used in the notebook. They will be displayed as interactive widgets in the sidebar. Each parameter should have a unique name that corresponds to the variable name used in the code.

## Define widget with YAML

#### Widget name is a variable name
Definition of the widget (in `params`) starts with the widget name. It will correspond to the variable in the code. The name should be a valid Python variable. 

#### Widget input type
The next thing is to select the input type. It can be: `text`, `slider`, `range`, `select`, `checkbox`, `numeric`, `file`. 

#### Widget label
For each input we need to define a `label`. It will be a text displayed above (or near) the widget.

#### Widget default value
You can set a default widget by setting the `value`. The format of the `value` depends on the input type:

- for `text` a `value` should be a string, example `value: example text`,
- for `slider` a `value` should be a number, example: `value: 5`,
- for `range` a `value` should be a list with two numbers, example `value: [3,6]`,
- for `select` with `mutli: False` a `value` should be a string, example `value: hey`,
- for `select` with `multi: True` a `value` should be a list of strings, example `value: [cześć, hi, hello]`,
- for `checkbox` a `value` should be a boolean (`True` or `False`), example: `value: True`,
- for `numeric` a `value` should be a number, example: `value: 10.2`.
- for `file` a `value` is not needed.

The rest of the parameters depend on the widget input type.

#### Text

Additional parameters:

- `rows` - the number of rows in the text area (default is set to 1),

Example YAML:

```yaml
params:
    my_variable:
        input: text
        label: This is text label
        value: some text
        rows: 2
```

<p align="left" >
  <img 
    alt="Mercury Text"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_text_input_2.png" width="35%" />
</p>


#### Slider

Additional parameters:

- `min` - the minimum value for the slider (default is set to 0),
- `max` - the maximum value for the slider (default is set to 100).

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

- `min` - the minimum value for the slider (default is set to 0),
- `max` - the maximum value for the slider (default is set to 100).

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

- `multi` - a boolean value that decides if the user can select several options (default is set to `False`).
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

#### File

Additional parameters:

- `maxFileSize` - a maximum allowed file size (default set to 100MB). The file size should be defined as a string with MB or KB at the end.

```yaml
params:
    filename:
        label: This is file label
        input: file
        maxFileSize: 1MB
```

<p align="left" >
  <img 
    alt="Mercury File"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_file_input.png" width="35%" />
</p>

The uploaded file name will be passed to the notebook as a string. The uploaded file will be copied to the same directory as the notebook. After notebook execution, the uploaded file will be removed.

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

To use variables in the code simply define the variable with the same name as the widget name. You can also assign the same value as defined in YAML. Please define all variables in one cell (it can be below the cell with YAML config).

When the user interacts with widgets and clicks the `Run` button, the code with variables will be updated with user selected values.

Example:

<p align="left" >
  <img 
    alt="Mercury Variables"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_variables.png" width="70%" />
</p>

## Output files

You can easily create files in your notebook and allow your users to download them.

You need to define an `output` directory in YAML header and in variables add variable with output directory name.

The example notebook:

1. The first RAW cell.
```yaml
title: My app
description: App with file download
params:
    output_dir:
        output: dir
```

2. The next cell should have a variable containing the directory name. The variable should be exactly the same as in YAML. This variable will have assigned a new directory name that will be created for your user during notebook execution. Please remember to define all variables that are interactive in Mercury in one cell, just after the YAML header (that's the only requirement to make it work, but very important).

```py
output_dir = "example_output_directory"
```

3. In the next cells, just produce files to the `output_dir`:

```py
import os
with open(os.path.join(output_dir, "my_file.txt"), "w") as fout:
    fout.write("This is a test")
```

In the Mercury application, there will be additional menu in the top with `Output files` button. Please click there to see your files. Each file in the directory can be downloaded.

![Output files in Mercury](https://user-images.githubusercontent.com/6959032/153185874-f24cd6fe-9c64-4fa5-8b41-3814856d330a.png)

## Welcome message

There is an option to set a custom welcome message. Like in the example screenshot below.

<p align="left" >
  <img 
    alt="Mercury Custom Welcome Message"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/custom_welcome_message.png" width="90%" />
</p>

The custom welcome message can be set as Markdown text (with GitHub flavour). To set custom message please create a `welcome.md` file and include your Markdown text there. When deploying please set the `WELCOME` environment variable pointing to your file. For example, in Heroku it will be `WELCOME=welcome.md`. The example repository with welcome message is [here](https://github.com/pplonski/data-science-portfolio). The example demo showing a Data Science Portfolio is [here](http://piotr-data-science-portfolio.herokuapp.com/).

If you don't set the welcome message a simple `Welcome!` will be displayed. We belive that setting welcome message will give you a great opportunity for customization.


## Installation

You can install Mercury directly from PyPi repository with `pip` command:

```
pip install mljar-mercury
```


## Running locally

To run Mercury locally just run:

```
mercury runserver --runworker
```

The above command will run server and worker. It will serve Mercury website at `http://127.0.0.1:8000`. It won't display any notebooks because we didn't add any. Please stop the Mercury server (and worker) for a moment with (Ctrl+C).

Execute the following command to add a notebook to Mercury database:

```
mercury add <path_to_notebook>
```


Please start the Mercury server to see your apps (created from notebooks).

```
mercury runserver --runworker
```


## Notebook development with automatic refresh

The Mercury `watch` command is perfect when you create a new notebook and want to see what it will look like as a web app with live changes.

Please run the following command:

```
mercury watch <path_to_your_notebook>
```

You can now open the web browser at `http://127.0.0.1:8000` and find your notebook. When you change something in the notebook code, markdown, or YAML configuration and save the notebook, then it will be automatically refreshed in the web browser. You can track your changes without manual refreshing of the web app.

## Mercury commands

### Add

Please use `add` command to add a notebook to the Mercury. It needs a notebook paath as an argument. 

Example:

```
mercury add notebook.ipynb
```

### Delete

Please use `delete` command to remove notebook from the Mercury. It needs a notebook path as an argument.

Example:

```
mercury delete notebook.ipynb
```

### List

Please use `list` command to display all notebooks in the Mercury.

Example:

```
mercury list
```

## Running in production

Running in production is easy. We provide several tutorials on how it can be done.

- [Deploy to Heroku](https://github.com/mljar/mercury/wiki/Deploy-to-Heroku) using free dyno 
- [Deploy to AWS EC2](https://github.com/mljar/mercury/wiki/Deploy-to-AWS-EC2) using t2.micro 
- Deploy to Digital Ocean (comming soon)
- Deploy to GCP (comming soon)
- Deploy to Azure (comming soon)

## Running with `docker-compose`

The `docker-compose` must be run from the Mercury main directory.

Please copy `.env.example` file and name it `.env` file. Please point the `NOTEBOOKS_PATH` to the directory with your notebooks. All notebooks from that path will be added to the Mercury before the server start. If the `requirements.txt` file is available in `NOTEBOOKS_PATH` all packages from there will be installed.

Please remember to change the `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD`.

To generate new `SECRET_KEY` (recommended), you can use:

```
python -c 'from django.core.management.utils import get_random_secret_key; \
            print(get_random_secret_key())'
```

Please leave `SERVE_STATIC=False` because in the `docker-compose` configuration static files are served with nginx.

The `docker-compose` will automatically read environment variables from `.env` file. To start the Mercury, please run:

```
docker-compose up --build
```

To run in detached mode (you can close the terminal) please run:
```
docker-compose up --build -d
```

To stop the containers:

```
docker-compose down
```

## Mercury development

The Mercury project consists of three elements:

- Frontend is written in TypeScript with React+Redux
- Server is written in Python with Django
- Worker is written in Python with Celery

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

The worker code is in the `mercury` directory (in the `apps/notebooks/tasks.py` and `apps/tasks/tasks.py` files). Please activate first the virtual environment (it is using the same virtual environment as a server):

```
source menv/bin/activate
```

Run the worker:
```
celery -A server worker --loglevel=info -P gevent --concurrency 1 -E
```

## Mercury Pro

Looking for dedicated support, a commercial-friendly license, and more features? The Mercury Pro is for you. Please see the details at [our website](https://mljar.com/pricing).


<p align="center">
  <img 
    alt="Mercury logo"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_logo_v1.png" width="30%" />
</p>
