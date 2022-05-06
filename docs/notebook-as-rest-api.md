<h1> Notebook as REST API </h1>

You can turn your notebook into REST API endpoint with Mercury. It is possible to trigger notebook execution with POST request. The notebook saves a response as JSON file. The GET endpoint fetch the response.

The example YAML configuration (it should be in the first raw cell)

```yaml
---
title: My endpoint
description: Notebook as REST API example
slug: hello
output: rest api
params:
    response_file:
        output: response
    name:
        input: text
        label: What is your name?
        value: Piotr
---
```

The second code cell should have variables from YAML configuration:

```python
response_file = "response.json"
name = "Piotr"
```

The final cell that saves the response:

```python
import json
with open(response_file, "w") as fout:
    fout.write(json.dumps({"msg": f"Hello {name}!"}))
```

When you open this notebook in the Mercury you will see special User Interface that helps you write endpoints calls.


<img 
    style="border: 1px solid #e1e4e5"
    alt="Notebook as REST API"
    src="../media/notebook-rest-api-view.png" width="100%" />
