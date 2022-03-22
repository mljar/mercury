<h1> Widgets </h1>

## Define widget with YAML

<h3> Widget name is a variable name </h3>
Definition of the widget (in `params`) starts with the widget name. It should correspond to the variable in the code (in the notebook). The name should be a valid Python variable. 

<h3> Widget input type </h3>
The widget is selected by `input` type. It can be: `text`, `slider`, `range`, `select`, `checkbox`, `numeric`, `file`. 

<h3> Widget label </h3>
For each widget we need to define a `label`. It will be a text displayed above (or near) the widget.

<h3> Widget default value </h3>
You can set a default value of the widget by setting the `value`. The format of the `value` depends on the input type:

- for `text` a `value` should be a string, example `value: example text`,
- for `slider` a `value` should be a number, example: `value: 5`,
- for `range` a `value` should be a list with two numbers, example `value: [3,6]`,
- for `select` with `mutli: False` a `value` should be a string, example `value: hey`,
- for `select` with `multi: True` a `value` should be a list of strings, example `value: [cześć, hi, hello]`,
- for `checkbox` a `value` should be a boolean (`True` or `False`), example: `value: True`,
- for `numeric` a `value` should be a number, example: `value: 10.2`.
- for `file` a `value` is not needed.

The rest of the parameters depend on the widget input type.

# Wdgets

### Text

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
    alt="Mercury Text Widget"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_text_input_2.png" width="30%" />
</p>


### Slider

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

### Range

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

### Select 

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

### Checkbox

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

### Numeric

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

### File

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

## Full example YAML

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


## Use variables in the code

To use variables in the code simply define the variable with the same name as the widget name. You can also assign the same value as defined in YAML. Please define all variables in one cell (it can be below the cell with YAML config).

When the user interacts with widgets and clicks the `Run` button, the code with variables will be updated with user selected values.

Example:

<p align="left" >
  <img 
    alt="Mercury Variables"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_variables.png" width="70%" />
</p>


