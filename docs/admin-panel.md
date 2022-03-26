<h1> Admin Panel </h1>

Admin Panel is the place where you can manage all things that are logged to the Mercury's database:

- add/delete/upade notebooks
- access to all tasks executed 
- add/delete/update users (only for Pro)
- add/detele/update groups (only for Pro)

### Set up Admin Panel

You need to define three environment variables during the deployment to access the Admin Panel. You can do this by adding them in `.env` file if you are using `docker-compose` method for [deployment](/deploy/deployment):

```
DJANGO_SUPERUSER_USERNAME=your_user_name
DJANGO_SUPERUSER_PASSWORD=your_secret_password
DJANGO_SUPERUSER_EMAIL=your_email
```

If you are not using `docker-compose` for deployment, then the process of setting environment variables depends on the cloud provider where you deploy the Mercury. For example in Heroku, you can set them with command line:

```
heroku config:set DJANGO_SUPERUSER_USERNAME=your_user_name
heroku config:set DJANGO_SUPERUSER_PASSWORD=your_secret_password
heroku config:set DJANGO_SUPERUSER_EMAIL=your_email
```

!!! note "Admin Panel locally"

    You can set Admin Panel when running Mercury locally. Please run the command `mercury createsuperuser` and follow the instructions on the terminal.
    
## Log in to Admin Panel

Please add `/admin` to your URL 