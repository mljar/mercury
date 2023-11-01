import json

from IPython.display import display

from .manager import WidgetsManager


class App:
    """
    The App widget controls how the notebook is displayed within Mercury.
    
    It provides configuration options for display features such as the title, 
    description, code visibility, update behavior, and more, allowing for a 
    customizable notebook presentation.

    Parameters
    ----------
    title : str, default 'Title'
        The title of the application. This is used in the home view and in the sidebar.
        If an empty string is provided, the notebook filename will be displayed.

    description : str, default 'Description'
        A description of the application. This is used in the home view.
        If an empty string is provided, no description will be displayed.

    show_code : bool, default False
        Set to True to display the notebook's code. The default is False, which means 
        the code is hidden.

    show_prompt : bool, default False
        If True, the notebook prompt will be shown in the application. Requires 
        `show_code` to be True as well. The default is False.

    output : str, default 'app'
        Determines the format of the notebook's output. The default is "app", 
        meaning the notebook will be displayed as an interactive web application. 
        If the notebook is detected to have presentation slides, the output format 
        automatically changes to "slides".

    schedule : str, default ''
        A cron schedule expression that determines how frequently the notebook is 
        run. The default is an empty string, meaning the notebook is not scheduled 
        to run automatically. The `schedule` must be a valid cron expression, and 
        its validity is checked upon notebook initialization.

    notify : dict, default {}
        A dictionary specifying notification settings. It determines the conditions 
        under which notifications should be sent and who should receive them. 

    continuous_update : bool, default True
        If True (the default), the notebook is recomputed immediately after a widget 
        value changes. Set to False to have updates occur after clicking a Run button.

    static_notebook : bool, default False
        When True, the notebook will not be recomputed on any widget change, making 
        the notebook static. The default is False, which means the app presented in 
        Mercury is interactive.

    show_sidebar : bool, default True
        Determines the visibility of the sidebar when the Mercury App is opened. 
        By default, the sidebar is displayed, but it can be hidden with this 
        parameter set to False.

    full_screen : bool, default True
        If True (the default), the notebook is displayed with full width. Set to 
        False to limit notebook width to 1140px.

    allow_download : bool, default True
        If True (the default), a Download button is available to export results as 
        a PDF or HTML file. Set to False to hide the Download button.

    stop_on_error : bool, default False
        If True, the notebook will stop execution when an error occurs in a cell. 
        The default is False, meaning the notebook will execute all cells even with 
        errors.

    Examples
    --------
    Constructing Mercury App with `title` and `description` arguments.
    >>> import mercury as mr
    >>> app = mr.App(title="Mercury Title", description="Mercury description")

    Constructing Mercury App to show notebook's code with `show_code` argument.
    >>> app = mr.App(title="Mercury Title", 
    ...              description="Mercury description", 
    ...              show_code=True)
    """

    def __init__(
        self,
        title="Title",
        description="Description",
        show_code=False,
        show_prompt=False,
        output="app",
        schedule="",
        notify={},
        continuous_update=True,
        static_notebook=False,
        show_sidebar=True,
        full_screen=True,
        allow_download=True,
        stop_on_error=False,
    ):
        self.code_uid = WidgetsManager.get_code_uid("App")
        self.title = title
        self.description = description
        self.show_code = show_code
        self.show_prompt = show_prompt
        self.output = output
        self.schedule = schedule
        self.notify = notify
        self.continuous_update = continuous_update
        self.static_notebook = static_notebook
        self.show_sidebar = show_sidebar
        self.full_screen = full_screen
        self.allow_download = allow_download
        self.stop_on_error = stop_on_error
        display(self)

    def __repr__(self):
        return f"mercury.App"

    def _repr_mimebundle_(self, **kwargs):
        data = {}
        data["text/plain"] = repr(self)
        data[
            "text/html"
        ] = "<h3>Mercury Application</h3><small>This output won't appear in the web app.</small>"
        view = {
            "widget": "App",
            "title": self.title,
            "description": self.description,
            "show_code": self.show_code,
            "show_prompt": self.show_prompt,
            "output": self.output,
            "schedule": self.schedule,
            "notify": json.dumps(self.notify),
            "continuous_update": self.continuous_update,
            "static_notebook": self.static_notebook,
            "show_sidebar": self.show_sidebar,
            "full_screen": self.full_screen,
            "allow_download": self.allow_download,
            "stop_on_error": self.stop_on_error,
            "model_id": "mercury-app",
            "code_uid": self.code_uid,
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)
        return data
