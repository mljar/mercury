<h1> Interactive Slides </h1>

You can easily create interactive slides from your notebook. Slides are created with [reveal.js](https://github.com/hakimel/reveal.js/). The interactive widgets are added by [Mercury](https://github.com/mljar/mercury) framework. You can go through the slides and change them dynamically by tweaking widgets values.

- To make slides from the notebook, please use the [RISE extenction](https://rise.readthedocs.io/en/stable/).
- To make slides interactive, please add the YAML configuration in the first cell.


### Full screen presentation

It is possible to enter the full screen mode. Please click anywhere in the presentation and press `k` on the keyboard. Press `Esc` to leave full screen mode.

### Slides preview

You can enter slides navigation by pressing `Esc` key. You can select any slide by clicking it.

### Example

The example YAML configuration for creating interactive slides:

```yaml
title: My app
description: My amazing app
output: slides
# ... the rest of the config ...
```


You can check the demo slides running at HuggingFace Spaces at [https://huggingface.co/spaces/pplonski/interactive-presentation](https://huggingface.co/spaces/pplonski/interactive-presentation).

<img 
    style="border: 1px solid #e1e4e5"
    alt="Interactive slides in Mercury"
    src="../media/interactive-slides-mercury-demo.gif" width="100%" />


### Themes

You can style apps with available themes.

#### Light themes:

- white (default)
- sky
- beige
- simple
- serif
- solarized

#### Dark themes: 

- black
- league
- blood
- night
- moon

To use the theme in the Mercury YAML configuration you need to define `format`. The example below:

```yaml
title: My app
output: slides
format:
    theme: night
# the rest of YAML ...
```

You can check slides themes online in [the app](https://slides-themes.herokuapp.com/).

### Themes gallery

![](https://github.com/mljar/mercury-slides-themes/raw/main/media/slides-themes-list.gif)

### Themes demo

![](https://github.com/mljar/mercury-slides-themes/raw/main/media/mercury-slides-themes.gif)


