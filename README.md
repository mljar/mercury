# Mercury v3 (Work in Progress)

This is a complete rewrite of Mercury with a new architecture.
The stable v2 codebase is available on the `v2.4.3` tag.

Mercury allows you to easily share your Python notebooks as interactive web apps. What is more, it offers set of beautiful widgets to help you build data rich apps, chats, AI agents, dashboards, reports.

The best part is that Python code is enough to create frontend. 

We tried to make this framework easy to use and easy to deploy.

Things that makes Mercury unique:

- no callbacks for widgets, after widget interaction all cells below updated are re-executed
- predefined layout, you can place widget in the sidebar, main view or footer
- live app preview in MLJAR Studio or JupyterLab editors
- welcome page with list of all notebooks


## Example

```python
# import package
from mercury import TextInput

# create widget
text = TextInput(label="What is your name?")

# display widget value
print(f"Hi {text.value} 👋")
```

## Keep Session

## Configuration and customization

## Authentication

## Deployment

## Examples

## Arguments

--log-level


## Notebook view in home page



