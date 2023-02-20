<h1> Deploy on Azure </h1>

The simplest way to get your Mercury application deployed on Azure is via the [Azure Developer CLI (`azd`)](https://aka.ms/azd), which surfaces high-level commands to help you go from local development environment to Azure cloud, quickly.

The Azure Developer CLI relies on application templates (think "cloud recipes" or blueprints) to provision resources and deploy your app. These templates include sample application code, Infrastructure as Code files (written in Bicep or Terraform) to provision Azure resources and deploy your code, some tool-specific files (e.g. `azure.yaml`), and more.

Azure Developer CLI templates are completely extensible, meaning that you can swap out the sample application code for your own and leverage the template's Infrastructure as Code files to go from functioning prototype to fully-fledged application on Azure, in a single step and in minutes.

Note: If you don't have an Azure subscription, you can sign up for a free account [here](https://azure.microsoft.com/en-us/free/).

## Install the Azure Developer CLI
You can find instructions on how to install the Azure Developer CLI via [https://aka.ms/azd-install](https://aka.ms/azd-install).

## Quickstart

The easiest way to get started is to start from an existing Azure Developer CLI-compatible template. For instance, if you start from a template like https://github.com/savannahostrowski/jupyter-mercury-aca, you really just have to:
    1. Add your Jupyter notebooks to the `src/` in the template
    2. Make sure you've installed the required dependencies for your notebooks
    3. Run `pip freeze > requirements.txt` to save the dependencies (relevant for building the container image)
    4. Run `azd up` in the project root (which will provision infrastructure on Azure based on Infrastructure as Code files in `infra/` and deploy the code to those resources)

After running `azd up`, you'll have a functioning web app up on Azure, hosted on Azure Container Apps.

As a note, other templates can be found on the Azure Developer CLI's [template gallery - awesome-azd](https://aka.ms/awesome-azd), or by checking out the [azd-templates topic on GitHub](https://github.com/topics/azd-templates).


## Build your own template
If, for some reason, the basic template above doesn't meet your needs, you can also make any repository Azure Developer CLI compatible. Instructions on how to do this can be found [here](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/make-azd-compatible?pivots=azd-create).


