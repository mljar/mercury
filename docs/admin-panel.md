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

Please add `/admin` to your server URL. For example, the mercury is running at: `https://mercury.mljar.com` then the Admin Panel address is `https://mercury.mljar.com/admin`. You should see the log in view:

<img 
    style="border: 1px solid #e1e4e5"
    alt="Log in view to Admin Panel"
    src="../media/admin_login.png" width="100%" />

Please provide the username and password used in setup and click `Log in` button.

!!! note "Running Mercury without domain"

    You can run Mercury without domain. You will enter the IP address to see the Mercury service. To view the Admin Panel you need to extend the IP address with `/admin`. For example, your Mercury instance is running at `54.30.24.211` then the Admin Panel is available at `54.30.24.211/admin`.

## Admin Panel view

After successful log in you will see the Admin Panel. Below is the view of Admin Panel in the open-source version and in the Pro version (available in [commercial license](https://mljar.com/pricing))

The open-source Admin Panel view:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel"
    src="../media/admin_panel.png" width="100%" />


The Pro Admin Panel view:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel Pro"
    src="../media/admin_panel_pro.png" width="100%" />    

## Notebooks

Please click `Notebooks` to see your notebooks available in the Mercury.

- To delete the notebook please select the notebook and select the action at the top of the list. 
- To update the notebook please click in the notebook id. The edit view will be available.
- There is option to add a notebook in the Admin Panel, but it is not recommended. Please use `mercury add` command to add notebooks to the Mercury.

The 
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel Notebooks"
    src="../media/admin_notebooks.png" width="100%" />    

## Users

Please click `Users` to see your users. You will see the view like in the screenshot below:

<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel users"
    src="../media/admin_users.png" width="100%" />    

To add a new user please click `ADD USER` button in the top right corner. You will see the view asking for username and password:

<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel add user"
    src="../media/admin_add_user.png" width="100%" />    

Please click `SAVE` you will be asked for personal information: first name, last name and email address.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel user personal info"
    src="../media/admin_personal_info.png" width="100%" />    

Please scroll down and fill the `Last login` time (click `Today` and `Now`). Please click `SAVE` button to have user account created. 

<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel add user save"
    src="../media/admin_add_user_save.png" width="100%" />    

## Groups

Mercury groups can be used to share a notebook with selected group of users. The first step is to create a group. Then users need to be added to the group by creating the membership.

The empty list of Merucry groups:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel group"
    src="../media/admin_groups.png" width="100%" />    

Please click `ADD MERCURY GROUP` and fill the form:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel add group"
    src="../media/admin_add_group.png" width="100%" />    

The view after adding a first group:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel group"
    src="../media/admin_group_added.png" width="100%" />    

## Membership

To add users in the group please create a Mercury membership.

The empty list of memberships:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel Memberships"
    src="../media/admin_memberships.png" width="100%" />    

Please click `ADD MEMBERSHIP` and select user and group:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel add membership"
    src="../media/admin_add_membership.png" width="100%" />    

The view after successfull creation of the membership:
<img 
    style="border: 1px solid #e1e4e5"
    alt="Admin Panel membership added"
    src="../media/admin_membership_added.png" width="100%" />    
