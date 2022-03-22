<h1> Welcome Message </h1>

There is an option to set a custom welcome message (instead of `Welcome!` in the home view). Like in the example screenshot below.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Custom Welcome Message"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/custom_welcome_message.png" width="100%" />

The custom welcome message can be set as Markdown text (with GitHub flavour). To set custom message please create a `welcome.md` file and include your Markdown text there. 

!!! note "Deployment"

    If you deploy with `mercury run` command then you don't need to do anything. Otherwise, please set the `WELCOME` environment variable with path to your welcome file.  

- The example repository with welcome message is [here](https://github.com/pplonski/data-science-portfolio). 
- The example demo showing a Data Science Portfolio is [here](http://piotr-data-science-portfolio.herokuapp.com/).

If you don't set the welcome message a simple `Welcome!` will be displayed. We belive that setting welcome message will give you a great opportunity for customization.
