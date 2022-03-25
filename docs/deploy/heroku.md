<h1> Deploy on Heroku </h1>

You can find an example repository at [GitHub](https://github.com/pplonski/mercury-simple-demo) and [demo app](http://mercury-simple-demo.herokuapp.com/) running on Heroku.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Mercury Demo App"
    src="https://raw.githubusercontent.com/pplonski/mercury-simple-demo/main/media/super-simple-web-app.gif" width="100%" />

## Setup GitHub repository 

Please create a new GitHub repository for your project and clone it to your machine. 

```
git clone git@github.com:pplonski/mercury-simple-demo.git
```

## Setup Heroku account and CLI 

In this guide, we assume that you have a Heroku account and Heroku CLI. 

- Heroku signup [page](https://signup.heroku.com/)
- Heroku command-line interface (CLI) installation [docs](https://devcenter.heroku.com/articles/heroku-cli)

In this guide, we will use **free** dyno. 

Please go to your project's directory and login to Heroku:

```
heroku login
```

Then, please create a new Heroku app:

```
heroku create mercury-simple-demo
```

You can also run `heroku create` and the Heroku service will create some random name for you. You can open your web app by running:

```
heroku open
```

## Prepare the notebook

The first step is to install Mercury:

```
pip install -U mljar-mercury
``` 

Please create the `requirements.txt` file and add there the `mljar-mercury` package and all packages needed by your notebooks (you can add several notebooks to Mercury).

The next step is to create a YAML config in your notebook ([docs](/yaml-parameters) about YAML construction). Use the following command to run the app in the Mercury:

```
mercury watch <path_to_your_notebook>
```

The Mercury is running locally at `http://127.0.0.1:8000`.

## Deploy to Heroku

Before deployment, we will need to create `Procfile` that will tell Heroku how to run Mercury. It will have one line:

```
web: mercury run 0.0.0.0:$PORT
```

In the `Procfile` we start the Mercury worker in the background and serve Django. Please add the `Procfile` to the GitHub repository:

```
git add Procfile
git commit -am "add heroku procfile"
git push
```

We are ready to deploy to Heroku. It can be done with:

```
git push heroku main
```

After that, you should be able to see the Mercury running your notebooks as apps. :)

## Update notebook 

If you want to update something, just edit your notebook and save it. Then commit updates to the git and you can deploy to Heroku again.

```
# after updates
git commit -am "save my important changes"
# push to GitHub
git push
# deploy to Heroku
git push heroku main
```
