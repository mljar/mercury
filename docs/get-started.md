<h1> Get started </h1>

In this section we will create a notebook and will share it as a web app.

#### Create a notebook

Let's create a simple notebook that will print `Hello Earth!`.

![](../media/create_notebook.png)

#### Define YAML header

Let's add a **RAW** cell at the beginning of the notebook. Please add YAML header there.

![](../media/notebook_with_yaml.png)


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

We define `title` and `description` - those values are used when displaying information about app in the app gallery. Additionally, the `title` is used in the side bar above the widgets.

In the `params` we define a single widget with the name `planet`. We set it's type to select widget (`input: select`). The text in the label above the widget is set with `label`. The default that is displayed by widget is `value: Earth`. The values in the select widgets are set with `choices`.

!!! note "Widgets names are variables names" 

    Please remember that widgets names should be the same as variables names. 

#### Run the app locally

To run app locally please use the command:

```
mercury run greetings.ipynb
```

Please open the web browser with address `http://127.0.0.1`.

![](../media/app_running_locally.png)

#### Deploy to the cloud


#### Share URL link  with non-technical users