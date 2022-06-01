<h1> Get started </h1>

In this section we will create a notebook and will share it as a web app.

#### Create a notebook

Let's create a simple notebook that will print `Hello Earth!`.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Create a notebook"
    src="../media/create_notebook.png" width="100%" />

#### Define YAML header

Let's add a **RAW** cell at the beginning of the notebook. Please add YAML header there.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Notebook with YAML"
    src="../media/notebook_with_yaml.png" width="100%" />

The YAML config:

```yaml
---
title: Hello 🌍🪐
description: Hello app
params:
    planet:
        input: select
        label: Please select a planet
        value: Earth
        choices: [Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune]
---
```

We define `title` and `description` - those values are used when displaying information about the app in the app-gallery. Additionally, the `title` is used in the side bar above the widgets.

In the `params` we define a single widget with the name `planet`. We set it's type to a select widget (`input: select`). The text in the label above the widget is set with `label`. The default value displayed by widget is `value: Earth`. The values in the select are set with `choices`.

!!! note "Widgets names are variables names" 

    Please remember that widgets names should be the same as variables names. 

#### Run the app locally

To run app locally please use the command:

```
mercury run greetings.ipynb
```

Please open the web browser with address `http://127.0.0.1:8000`.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Run app locally"
    src="../media/app_running_locally.png" width="100%" />

If you would like to run a `mercury` locally on different port please specify it in the `run` command:

```
mercury run greetings.ipynb 127.0.0.1:<your-port>
```

There are many ways in which the app can be deployed to the cloud. Please check the [Deployment](/deploy/deployment) section.