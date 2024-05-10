import json

from IPython.display import display

from .manager import WidgetsManager
from .json import JSON 

class APIResponse:
    """
    The APIResponse class provides an interface for returning JSON response from notebook.
    Notebook can be executed with REST API and can return the JSON response.

    Attributes
    ----------
    response : dict, default {}
        JSON response from notebook.

    Examples
    --------
    Returning JSON response from notebook.
    >>> import mercury as mr
    >>> my_response = mr.APIResponse(response={"msg: "hello from notebook"})
    """
    def __init__(self, response={}):
        if not isinstance(response, dict):
            raise Exception("Please provide response as dict {}")
        self.code_uid = WidgetsManager.get_code_uid("APIResponse")
        self.response = response
        JSON(response, level=4)     
        display(self)   

    @property
    def value(self):
        return self.response

    def __str__(self):
        return "mercury.APIResponse"

    def __repr__(self):
        return "mercury.APIResponse"

    def _repr_mimebundle_(self, **kwargs):
        data = {}

        view = {
            "widget": "APIResponse",
            "value": json.dumps(self.response),
            "model_id": self.code_uid,
            "code_uid": self.code_uid,
        }
        data["application/mercury+json"] = json.dumps(view, indent=4)

        data["text/plain"] = "API Response"

        return data
