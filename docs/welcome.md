# Welcome Message

There is an option to set a custom welcome message (instead of `Welcome!` in the home view). Like in the example screenshot below.

<p align="left" >
  <img 
    alt="Mercury Custom Welcome Message"
    src="https://raw.githubusercontent.com/mljar/visual-identity/main/mercury/custom_welcome_message.png" width="90%" />
</p>

The custom welcome message can be set as Markdown text (with GitHub flavour). To set custom message please create a `welcome.md` file and include your Markdown text there. When deploying please set the `WELCOME` environment variable pointing to your file. For example, in Heroku it will be `WELCOME=welcome.md`. The example repository with welcome message is [here](https://github.com/pplonski/data-science-portfolio). The example demo showing a Data Science Portfolio is [here](http://piotr-data-science-portfolio.herokuapp.com/).

If you don't set the welcome message a simple `Welcome!` will be displayed. We belive that setting welcome message will give you a great opportunity for customization.
