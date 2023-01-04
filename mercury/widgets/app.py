import json

from IPython.display import display


class App:
    def __init__(self, title, description, 
        show_code=False, show_prompt=False, share="",
        output="app", slug="", schedule="", notify={}):
        self.title = title
        self.description = description
        self.show_code = show_code
        self.show_prompt = show_prompt
        self.share = share 
        self.output = output
        self.slug = slug
        self.schedule = schedule
        self.notify = notify
        display(self)

    def __repr__(self):
        return f'mercury.App'

    def _repr_mimebundle_(self, **kwargs):
        data = {}
        data["text/plain"] = repr(self)
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
            "model_id": "mercury-app",
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)
        return data
