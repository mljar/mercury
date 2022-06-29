<h1> Configuration </h1>

The `Mercury` can be configured with environment variables. There are several ways to provide them. 

- you can set them manually,
- you can set them when starting the `mercury`,
- you can provide them in `.env` file (the prefered way).

## List of environment variables

- `DEBUG` - (boolean) run server in debug mode. Example `DEBUG=False`.
- `SERVE_STATIC` - (boolean) let the Django server serves the static files, example `SERVE_STATIC=False`
- `DJANGO_SUPERUSER_USERNAME` - (string) admin username, used to login to [Admin Panel](/admin-panel). Example `DJANGO_SUPERUSER_USERNAME=piotr`
- `DJANGO_SUPERUSER_PASSWORD` - (string) admin password, used to login to [Admin Panel](/admin-panel). Example `DJANGO_SUPERUSER_PASSWORD=secret-one`.
- `DJANGO_SUPERUSER_EMAIL` - (string) admin email. Example `DJANGO_SUPERUSER_EMAIL=piotr@example.com`.
- `SECRET_KEY` - (string) Django secret key. Example `SECRET_KEY="x3%q8fs(-q3i(m&=e1g%9xtvcn*q!c%i@v0*ha4@ow2crdktpw"`
- `ALLOWED_HOSTS` - (string, list of string comma separated) a list of allowed hosts to make API calls to the server. Example `ALLOWED_HOSTS=mljar.com,12.10.12.30,mercury.mljar.com`.
- `WELCOME` - (string) - file path with custom welcome message (see [docs](/welcome)). Example `WELCOME=/path/to/file/welcome.md`.
- `EMAIL_HOST` - (string) string with email SMTP server address - it is used for email notifications when execute scheduled notebooks (see [docs](/schedule)). Example `EMAIL_HOST=smtp.gmail.com`.
- `EMAIL_HOST_USER` - (string) email address from which emails will be sent. Example `EMAIL_HOST_USER=piotr-exmaple-email@gmail.com`.
- `EMAIL_HOST_PASSWORD` - (string) email password. For Gmail please use [app password](https://support.google.com/mail/answer/185833). Example `EMAIL_HOST_PASSWORD=some-password`.
- `EMAIL_PORT` - (number) email server port number. Example `EMAIL_PORT=587`.
- `DEFAULT_FROM_EMAIL` - (string) email address from whome email was sent. Example `DEFAULT_FROM_EMAIL=piotr-exmaple-email@gmail.com`.