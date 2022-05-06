<h1> Notebook as REST API </h1>

You can turn your notebook into REST API endpoint with Mercury. It is possible to trigger notebook execution with POST request. The notebook saves a response as JSON file. The GET endpoint fetch the response.

## Notebook 

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

## Endpoints

Based on the `slug` variable the endpoint is created with following template:

```
<server-address>/run/<slug>
```

For the `slug: hello`. There will be an endpoint (running on local server):

```
http://127.0.0.1:8000/run/hello
```

For this endpoint you can set POST request with parameters that are defined in YAML. For example:

```
curl -X POST -H "Content-Type: application/json" -d '{"name":"Piotr"}' http://127.0.0.1:8000/run/hello
```

The response will be an `id` of the task. Example response:

```
{"id": "id-with-some-random-string"}
```

It will be used to fetch the result:

```
curl http://127.0.0.1:8000/get/id-with-some-random-string
```

If notebook was executed, the response will have JSON content:

```
{"msg": "Hello Piotr!"}
```

If the notebook is still in the execution the response will be:

```
{"state": "running"}
```

## User Interface

Please open the notebook in the Mercury to see special User Interface that will help you with endpoints usage. You can change values in the sidebar and curl commands will be updated.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Notebook as REST API"
    src="../media/notebook-rest-api-view.png" width="100%" />
