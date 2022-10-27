<h1> Deploy on Hugging Face Spaces</h1>

You can deploy notebooks with [Mercury](https://github.com/mljar/mercury) on [Hugging Face Spaces](https://huggingface.co/) (HF Spaces). 

## Create a new Space

Please create a new Space by filling the form at [https://huggingface.co/new-space](https://huggingface.co/new-space). As app type please select the `Gradio`. There is no official integration (yet!) of Mercury on HF Spaces.

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Create a new Hugging Face Space"
    src="../../media/create-new-space.png" width="100%" />
</p>


The Space that I'm using in this tutorial is available at the address [https://huggingface.co/spaces/pplonski/deploy-mercury](https://huggingface.co/spaces/pplonski/deploy-mercury).

## Add requirements.txt

Please create (`Add file` -> `Create a new file`) or upload (`Add file` -> `Upload file`) a new file `requirements.txt`. Please add there all required packages. I will add there `mljar-mercury` package as a requirement.

```
mljar-mercury
```

## Create app.py file 

You will need to add two files to run the Mercury. The first file is the `app.py` file that will start the Mercury server.

```python
import os
from dotenv import load_dotenv
from subprocess import Popen
load_dotenv()

command = ["mercury", "run", f"0.0.0.0:{os.environ.get('PORT', 7860)}"] 
worker = Popen(command) 
worker.wait()
```

The file `app.py` can be added at HF Space website (`Add file` -> `Create a new file`) or uploaded (`Add file` -> `Upload file`). The `Add file` button is available at `Files and versions` tab.

## Upload the notebook

Please upload the notebook with Mercury YAML configuration in the first RAM cell. It can be done with `Add file` -> `Upload file`. The file that I upload is called `demo.ipynb` and is simple notebook that display greetings.

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Greetings Notebook with YAML config"
    src="../../media/greetings-notebook.png" width="100%" />
</p>

## Running the app

After successfull build, you should be able to click `App` on the top left corner. The application should be ready to use.

<p>
  <img 
    style="border: 1px solid #e1e4e5"
    alt="Interactive Notebook with Mercury on Hugging Face Space"
    src="../../media/mercury-hugging-face-spaces.gif" width="100%" />
</p>

The interesting thing is that you can run standalone web app from HF. Just need to define new URL with your username and space.


My space link is: [https://huggingface.co/spaces/pplonski/deploy-mercury](https://huggingface.co/spaces/pplonski/deploy-mercury) based on my username (`pplonski`) and Space name (`deploy-mercury`) I construct the link: [https://pplonski-deploy-mercury.hf.space](https://pplonski-deploy-mercury.hf.space). This link can be used for example for embedding notebooks on the website like below:


<iframe src="https://pplonski-deploy-mercury.hf.space/app/1" height="700px" width="1200px" style="border: 1px solid #aaa"></iframe>


The code to create embedded notebook:

```html
<iframe 
    src="https://pplonski-deploy-mercury.hf.space/app/1" 
    height="700px" 
    width="1200px" 
    style="border: 1px solid #aaa">
</iframe>
```
