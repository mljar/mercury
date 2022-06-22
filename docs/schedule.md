<h1> Schedule notebook </h1>

You can schedule notebook to be executed in time intervals with `schedule` parameter in the YAML config. Please specify the time interval with crontab string. You can check the crontab string in the [crontab.guru](https://crontab.guru) website.

Example YAML config to execute the notebook on [every Monday at 8:00](https://crontab.guru/#0_8_*_*_1):

```
---
title: My notebook
description: My notebook executed automatically
schedule: '0 8 * * 1'
---
```

!!! note "crontab string should be in quote" 

    Please remember to use quotes when defining the `schedule`. 


## Timezone

You can set the timezone by defining the environment variable `TIME_ZONE`. It can be defined in `.env` variable. [Here](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568) is the list of available timezones.

## Notifications

For notebooks that are using `schedule` you can set automatic email notifications. It can be defined in the YAML configuration with the `notify` parameter:

```yaml
---
title: My notebook
description: My notebook executed automatically
schedule: '0 8 * * 1'
notify:
    on_success: email1@example.com, email2@example.com, username1
    on_failure: email1@example.com, username2
    attachment: html, pdf
---
```

You can decide who will be notified about successful or failure execution. You can define persons as emails or usernames. There in an option to add attachment to the email. The HTML or PDF with executed notebook is added to the email.

You need to setup the email settings to make notification works. It requires quite many parameters but don't be scared. It is easy to setup.

You need to set following environment values:

```
EMAIL_HOST
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD 
EMAIL_PORT
DEFAULT_FROM_EMAIL
```


Example:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=my-email@gmail.com
EMAIL_HOST_PASSWORD=secret-password
EMAIL_PORT=587
DEFAULT_FROM_EMAIL=my-email@gmail.com
```

