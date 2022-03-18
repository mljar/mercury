# YAML Parameters

Allowed parameters in the YAML config:

- `title` - string with a title of the notebook. It is used in the app sidebar and the gallery view.
- `author` - string with a author name (optional).
- `description` - string describing the content of the notebook. It is used in the gallery view.
- `show-code` - can be `True` or `False`. Default is set to `True`. It decides if the notebook's code will be displayed or not.
- `show-prompt` - can be `True` or `False`. Default is set to `True`. If set to `True` prompt information will be displayed for each cell in the notebook.
- `params` - the parameters that will be used in the notebook. They will be displayed as interactive widgets in the sidebar. Each parameter should have a unique name that corresponds to the variable name used in the code.