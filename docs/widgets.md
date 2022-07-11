<h1> Widgets </h1>

## Define widget with YAML

<h3> Widget name is a variable name </h3>
Definition of the widget (in `params`) starts with the widget name. It should correspond to the variable in the code (in the notebook). The name should be a valid Python variable. 

In the below example, the `variable_name` is the name of variable in the code and it is a widget name:
```yaml
params:
    variable_name:
        input: text
        label: Please provide the text
```

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

<h3>Output widgets</h3>

You can specify Markdown text in the sidebar. The syntax is as following:

```yaml
params:
    some_text:
        output: markdown
        value: | 
            ## header

            This is Markdown text in the sidebar. 

            - one
            - two
            - three
```

# Widgets

### Text

Available parameters:

- `input: text` - defines the text widget,
- `label` - the label above the widget,
- `value` - the default value of the widget, should be a string,
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

The widget view:

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Text Widget"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_text_input_2.png" width="50%" />
</p>


### Slider

Available parameters:

- `input: slider` - defines the slider widget,
- `label` - the label above the widget,
- `value` - the default value of the widget, should be a number,
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

The slider view:
<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Slider"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_slider.png" width="55%" />
</p>

### Range

Available parameters:

- `input: range` - defines the range widget,
- `label` - the label above the widget,
- `value` - the default value of the widget, should be list of two numbers, for example: `[3, 6]`,
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
<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Range"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_range.png" width="55%" />
</p>

### Select 

Available parameters:

- `input: select` - defines the select widget,
- `label` - the label above the widget,
- `multi` - a boolean value that decides if the user can select several options (default is set to `False`).
- for `mutli: False` a `value` should be a string, example `value: hey`,
- for `multi: True` a `value` should be a list of strings, example `value: [cześć, hi, hello]`,
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

The select view:

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Select"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_select.png" width="55%" />
</p>

### Checkbox

Available parameters.

- `input: checkbox` - defines the checkbox widget,
- `label` - the label above the widget,
- `value` - should be a boolean (`True` or `False`), example: `value: True`,

Example YAML:

```yaml
params:
    checkbox_variable:
        label: This is checkbox label
        input: checkbox
        value: True
```

The checkbox view:

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Checkbox"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_checkbox.png" width="55%" />
</p>

### Numeric

Available parameters:

- `input: numeric` - defines the numeric widget,
- `label` - the label above the widget,
- `value` - should be a number, example: `value: 5.5`.
- `min` - a minimum allowed value. There will be no minimum if not set.
- `max` - a maximum allowed value. There will be no maximum if not set.
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

The numeric view

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Numeric"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_numeric.png" width="55%" />
</p>

### File Upload

Available parameters:

- `input: file` - defines the file widget,
- `label` - the label above the widget,
- `maxFileSize` - a maximum allowed file size (default set to 100MB). The file size should be defined as a string with MB or KB at the end.

```yaml
params:
    filename:
        label: This is file label
        input: file
        maxFileSize: 1MB
```

The file upload view:

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury File"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_file_input.png" width="55%" />
</p>

The uploaded file name will be passed to the notebook as a string. The uploaded file will be copied to the same directory as the notebook. After notebook execution, the uploaded file will be removed.

## Example YAML

The example YAML with several widgets:

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

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury widgets"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_widgets.png" width="55%" />
</p>


## Widgets to variables   

To use widgets as variables in the code simply define the variable with the same name as the widget name. You can also assign the same default value as defined in the YAML. Please define all variables in one cell (it can be below the cell with YAML config).

When the user interacts with widgets and clicks the `Run` button, the code with variables will be updated with user selected values.

Example:

<p align="left" >
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Variables"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/mercury_variables.png" width="80%" />
</p>


