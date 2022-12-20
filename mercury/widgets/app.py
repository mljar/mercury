import json
from IPython.display import display


class App:
    def __init__(self, title, description, show_code=False):
        self.title = title
        self.description = description
        self.show_code = show_code
        display(self)

    def __repr__(self):
        return f'mercury.App(title="{self.title}", description="{self.description}", show_code={self.show_code})'

    def _repr_mimebundle_(self, **kwargs):
        data = {}
        data["text/plain"] = repr(self)
        view = {
            "widget": "App",
            "title": self.title,
            "description": self.description,
            "show_code": self.show_code,
            "model_id": "mercury-app",
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)
        return data
