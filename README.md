#### Environment Variables

ADMIN_EMAILS - Comma separated list of admin/dev emails to send error emails to.

APP_SETTINGS - Class in config.py to initialize with. config.DevelopmentConfig for development server and config.ProductionConfig for production.

DATABASE_URL - Postgres DB url

EMAIL_ADDR - Email address from which the app will send emails and notifications (i.e. no-reply@basicapp.com).

EMAIL_NAME - The name under which these emails will show in the recipients inbox (i.e. 'Basic App')

FLASK_APP=application.py

FLASK_ENV=development

SECRET_KEY - Use script below to generate a secret key.

SENDGRID_API_KEY - Sendgrid API key.

In some situations you will need to set the language for Click to run properly. You can do this in AWS, for example, with the following env vars:

LANG - en_US.utf-8

LC_ALL - en_US.utf-8

#### Generate Secret Key

The following script generates a random string of 64 letters (upper or lowercase), special characters, and numbers. This can be used for a secret key.

```python
import random
import string

chars = string.ascii_letters + string.digits + string.punctuation
print(''.join(random.choice(chars) for i in range(64)))
```

#### Set up DB

Simply run the following lines:
```
flask db init
flask db migrate
flask db upgrade
```

#### Execute CLI script

An example CLI script is included in this basic app. It sets a user as admin by the given email.
```
flask user make-admin admin@basic-app.com
```

### AWS Configuration

1. [Create a new ElasticBeanstalk application](https://console.aws.amazon.com/elasticbeanstalk/home#/gettingStarted?applicationName=getting-started-app)
    1. Choose preconfigured python for the platform. As of my last check, the docker version runs python 3.4 and you need 3.6 for this app.
    1. Once the application has been built navigate to Configuration -> Software.
        1. Under Static files set the /static/ path to the app/static/ directory.
        1. Set all the env vars under Environment properties. 
1. [Create a new CodePipeline](https://console.aws.amazon.com/codesuite/codepipeline/pipeline/new)
    1. **NOTE: Skip the build stage. You only need to connect your source directly to the EB application you just made.
    1. For the deploy step, select AWS Elastic Beanstalk and then your application. 
1. Configure SSL (or comment out SSLify in app/__init__.py to skip these steps)
    1. [Request a certificate](https://us-west-1.console.aws.amazon.com/acm/home)
    1. Configure the proper DNS settings (in addition to the CNAME records, you'll probably also want to put in a http -> https redirect)
    1. Under Configuration for your Elastic Beanstalk instance, select modify Capacity. Change the Environment type to 'Load balanced.'
    1. Save changes. Bak under Configuration, select modify Load balancer. 
    1. Add listener with the following settings.
        1. Listener port: 443
        1. Protocol: https
        1. Instance port: 80
        1. Instance protocol: http
        1. Select the certificate you created in step 3.i
    1. Enable session stickiness


#### TODOs
 - Separate .flaskenv (pushable) and .env (private) env vars.
 - Add custom error messaging for push notifications to error logging app.
 - Upload profile image. On new image/image delete, delete old file from S3
 - Configure for deployment to AWS Elasticbeanstalk (.ebextensions, etc.)
 - Configure for deployment to Heroku (Procfile, etc.)