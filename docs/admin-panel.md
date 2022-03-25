


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
