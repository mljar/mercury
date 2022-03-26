<h1> Frequently Asked Questions </h1>

If you don't find answer for your questions please open a [new issue](https://github.com/mljar/mercury/issues/new) or contact us by email contact@mljar.com.


<h4> How to generate a new Django SECRET_KEY </h4>

For better security please set your own SECRET_KEY. You can set it by defining the `SECRET_KEY` environment variable. It can be done in `.env` file if you are using `docker-compose` for deployment.

You can generate a new `SECRET_KEY` with the following command:

```
python -c 'from django.core.management.utils import get_random_secret_key; \
            print(get_random_secret_key())'
```

<h4> Is there an academic/research discount for a commercial license? </h4>

Yes, there is 50% discount for commercial license for academic and research use cases. Please contact us by email contact@mljar.com to get the coupon code. Please describe in the email at which university are you, what are you working on, and how would you like to use the Mercury.


<h4> Do I need make my notebooks code as open-source when using Mercury open-source version? </h4>

No. You can keep the notebook's code private. You don't have to make it open-source. You can share the notebook with open-source version of Mercury with parameter `show-code: False` so no one can see your code. But please remember that all users with link to the server where Mercury is running will be able to view your apps and execute them. If you would like to hide apps (notebooks) in the Mercury web app you need to have a commercial license which provides the [authentication](/authentication).
