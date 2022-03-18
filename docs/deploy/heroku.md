# Deploy on Heroku

You can find an example repository at [https://github.com/pplonski/mercury_demo_1](https://github.com/pplonski/mercury_demo_1).

The Mercury deployed with example notebooks at [https://mercury-demo-1.herokuapp.com/](https://mercury-demo-1.herokuapp.com/) (if no notebooks are loaded please refresh the website - it's a free dyno that sometimes sleeps).

## Please setup GitHub repository 

Please set a GitHub repository for your project. Please do the below steps in your directory (that is a GitHub repository).

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
heroku create your_app_name
```

If you can also run `heroku create` and the Heroku service will create some random name for you. Please remember the URL of your app. You can open it by running:

```
heroku open
```

## Prepare the notebook

The first step is to install Mercury:

```
pip install -U mljar-mercury
``` 

Please create the `requirements.txt` file and add there the `mljar-mercury` package and all packages needed by your notebooks (you can add several notebooks to Mercury).

The next step is to create a YAML config in your notebook ([docs](https://github.com/mljar/mercury#convert-notebook-to-web-app-with-yaml) about YAML construction). You can use the following command to observe how the notebook app will look like in the Mercury:

```
mercury watch <path_to_your_notebook>
```

You can see the Mercury running at `http://127.0.0.1:8000`.

## Prepare the `.env` file

Please add the `.env` file in your main directory. The example content:

```
SERVE_STATIC=True
ALLOWED_HOSTS=mercury-demo-1.herokuapp.com
NOTEBOOKS=/app/*.ipynb
```

Please set `ALLOWED_HOSTS` to your app address. In my case, it was `mercury-demo-1.herokuapp.com`. I set the `NOTEBOOKS` variable to point all `*ipynb` files in the project directory. The `/app/` directory is used because it is a path of notebooks after deploying to Heroku.

We need to set our environment variables in the Heroku dyno. We can do this by running the following command:

```
heroku config:set SERVE_STATIC=True
```

This needs to be repeated for all variables. The alternative is to use the following command that will set all env variables from the `.env` file:

```
heroku config:set $(cat .env | sed '/^$/d; /#[[:print:]]*$/d')
```

:warning: :warning: :warning: **Please do not commit `.env` to your GitHub repository** :warning: :warning: :warning:

## Deploy to Heroku

Before deployment, we will need to create `Procfile` that will tell Heroku how to run Mercury. It will have one line:

```
web: mercury runserver --runworker 0.0.0.0:$PORT
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
git commit -am "save my important changes
# push to GitHub
git push
# deploy to Heroku
git push heroku main
```

## Admin Panel

To access the Admin Panel in the Mercury you need to define three more variables in `.env` file:

```
DJANGO_SUPERUSER_USERNAME=your_user_name
DJANGO_SUPERUSER_PASSWORD=your_secret_password
DJANGO_SUPERUSER_EMAIL=your_email
```

Please add the above to the `.env` and to the Heroku with `heroku config:set` command.

## Django SECRET_KEY

For better security please set your own SECRET_KEY in `.env` file and apply changes to Heroku.

My example `.env` file:
```
SERVE_STATIC=False
DJANGO_SUPERUSER_USERNAME=piotr
DJANGO_SUPERUSER_PASSWORD=secret
DJANGO_SUPERUSER_EMAIL=piotr@piotr.pl
SECRET_KEY="x3%q8fs(-q3i(m&=e1g%9xtvcn*q!c%i@v0*ha4@ow2crdktpw"
```

You can generate `SECRET_KEY` with the following command:

```
python -c 'from django.core.management.utils import get_random_secret_key; \
            print(get_random_secret_key())'
```
