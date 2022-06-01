<h1> YAML Parameters </h1>

The YAML should be defined in the first RAW cell in the notebook. It controls how the notebook will be converted to the web app. The main things controlled by the YAML header:

- The way the app is displayed in the Mercury (`title` and `description`). 
- Decision to show or hide the code (`show-code`).
- Who can view the notebook (`share`).
- List of interactive widgets (`widgets`).

The list of allowed parameters in the YAML config:

- `title` - string with a title of the notebook. It is used in the app sidebar and the gallery view.
- `author` - string with a author name (optional).
- `description` - string describing the content of the notebook. It is used in the gallery view.
- `show-code` - can be `True` or `False`. Default is set to `True`. It decides if the notebook's code will be displayed or not.
- `show-prompt` - can be `True` or `False`. Default is set to `True`. If set to `True` prompt information will be displayed for each cell in the notebook.
- `share` - the comma separated list of users that can see the notebook. Default is set to `public` which means that all users can see the notebook. It can be set to `private` which means that only authenticated users can see the notebook. It can be set to the list of users, for example `username1, username2, username3`, which means that only users with username on the list can see the notebook. The last option is list the groups of users that can see the notebook, for example `group1, group2` - all users in the `group1` and `group2` will be able to see the notebook. You can mix group names and user names in the `share` parameter. The users and groups should be created in the Admin Panel. The sharing feature is only available to commercial users. 
- `output` - the type of the resulting notebook. It can be `app` or `slides` or `rest api`. The default is set to `app`.
- `slug` - the endpoint name at which the notebook as REST API will be available. Please see [REST API docs](/notebook-as-rest-api) for details.
- `schedule` - the string with crontab time interval that will be used to automatically execute the notebook. Please read more in [schedule docs](/schedule).
- `notify` - controls who will be notified be email after automatic notebook execution. Used only when `schedule` is defined. Please read more in [schedule docs](/schedule).
- `params` - the widgets that will be used in the notebook. They will be displayed in the sidebar. Each parameter should have a unique name that corresponds to the variable name used in the code. Please read more about available widgets in the [next secion](/widgets).