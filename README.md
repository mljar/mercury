```
     _ __ ___   ___ _ __ ___ _   _ _ __ _   _
    | '_ ` _ \ / _ \ '__/ __| | | | '__| | | |
    | | | | | |  __/ | | (__| |_| | |  | |_| |
    |_| |_| |_|\___|_|  \___|\__,_|_|   \__, |
                                         __/ |
                                        |___/ 
```

# Mercury 

Mercury is a framework that helps you build interactive web applications directly from Python notebooks. You can build with Mercury data rich applications, like: chats, AI agents, dashboards and reports.

## Why?

Mercury is the easiest way to built and deploy data rich apps with Python. There are no callbacks in the framework. **Widget interactions fire cells re-execution** (reactive notebooks). You don't need to worry about UI because there is **predefined layout**, so it will look beautiful.

Mercury use hidden gems of JupyterLab environment `ipywidgets` & `anywidget` to make easy to use and powerful web app framework.

## Example - Echo chat bot

Example bot app that will respond with echo:

```python
# import package
import mercury as mr
```

```python
# create Chat widget
chat = mr.Chat()
```

```python
# create chat prompt
prompt = mr.ChatInput()
```

```python
if prompt.value:
    # user message
    user_msg = mr.Message(prompt.value, role="user")
    chat.add(user_msg)

    # assistant message (echo)
    response_msg = mr.Message(
        f"Echo: {prompt.value}",
        role="assistant",
        emoji="🤖",
    )
    chat.add(response_msg)
```

### Live App Preview

Yes, you can preview the app during development.

![](https://raw.githubusercontent.com/mljar/mercury/refs/heads/v3/docs/src/assets/examples/basic-echo-chat.png)

### Production App

You can serve your notebook as standalone web app:

![](https://raw.githubusercontent.com/mljar/mercury/refs/heads/v3/docs/src/assets/examples/basic-echo-chat-web-app.png)

## Installation

```
pip install mercury
```

Start server with the following command:

```
mercury
```

It will detect all notebooks in the current directory and serve them as web apps.

Example view of notebooks home page:
![](https://raw.githubusercontent.com/mljar/mercury/refs/heads/v3/docs/src/assets/examples/notebooks-home.png)


The Mercury live app preview extension is available only for JupyterLab and MLJAR Studio. It will not work in Google Colab and VS Code - sorry guys!

## Deployment

Here is minimal Dockerfile to serve Mercury:
```docker
FROM python:3.12-slim

# Install Mercury
RUN pip install mercury==3.0.0a2

# You can also install needed packages here,
# For example install pandas
# RUN pip install pandas

# Directory where notebooks will be mounted
WORKDIR /workspace

# Mercury default port
EXPOSE 8888

# Start Mercury server
CMD ["mercury", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
```

We also offer **managed cloud** service for 1-click app deployment. Please check our website [platform.mljar.com](https://platform.mljar.com).

## Keep Session

## Configuration and customization

## Authentication



## Arguments

--log-level

--keepSession


## Notebook view in home page



The stable v2 codebase is available on the `v2.4.3` tag.