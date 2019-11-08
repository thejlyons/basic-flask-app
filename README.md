#### Environment Variables

ADMIN_EMAILS - Comma separated list of admin/dev emails to send error emails to.
APP_SETTINGS - Class in config.py to initialize with. config.DevelopmentConfig for development server and config.ProductionConfig for production.
DATABASE_URL - Postgres DB url
EMAIL_ADDR - Email address from which the app will send emails and notifications (i.e. no-reply@basicapp.com).
EMAIL_NAME - The name under which these emails will show in the recipients inbox (i.e. 'Basic App')
FLASK_APP=application.py
FLASK_ENV=development
SECRET_KEY=V*C5m_!S|5e^S6oGYCRRMm3n.z6eUK_nB]VjBD]fix:,|W0}a[pJE<4B}k,}{wk[
SENDGRID_API_KEY=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

#### Generate Secret Key

The following script generates a random string of 64 letters (upper or lowercase), special characters, and numbers. This can be used for a secret key.

```python
import random
import string

chars = string.ascii_letters + string.digits + string.punctuation
print(''.join(random.choice(chars) for i in range(64)))
```