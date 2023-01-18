import json

from IPython.display import display

from .manager import WidgetsManager


class App:
    def __init__(
        self,
        title="",
        description="",
        show_code=False,
        show_prompt=False,
        share="public",
        output="app",
        slug="",
        schedule="",
        notify={},
        continuous_update=True,
        static_notebook=False,
    ):
        self.code_uid = WidgetsManager.get_code_uid("App")
        self.title = title
        self.description = description
        self.show_code = show_code
        self.show_prompt = show_prompt
        self.share = share
        self.output = output
        self.slug = slug
        self.schedule = schedule
        self.notify = notify
        self.continuous_update = continuous_update
        self.static_notebook = static_notebook
        display(self)

    def __repr__(self):
        return f"mercury.App"

    def _repr_mimebundle_(self, **kwargs):
        data = {}
        data["text/plain"] = repr(self)
        data["text/html"] = "<h3>Mercury Application</h3><small>This output won't appear in the web app.</small>"
        view = {
            "widget": "App",
            "title": self.title,
            "description": self.description,
            "show_code": self.show_code,
            "show_prompt": self.show_prompt,
            "share": self.share,
            "output": self.output,
            "slug": self.slug,
            "schedule": self.schedule,
            "notify": json.dumps(self.notify),
            "continuous_update": self.continuous_update,
            "static_notebook": self.static_notebook,
            "model_id": "mercury-app",
            "code_uid": self.code_uid,
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)
        return data
