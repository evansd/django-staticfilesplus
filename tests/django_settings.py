# Minimal settings needed to persude the tests to run

SECRET_KEY = '4'
STATIC_URL = '/'

INSTALLED_APPS = (
    'django.contrib.staticfiles',
)

# This is only required for Django 1.4 where we have to use a TransactionTestCase
# instead of a SimpleTestCase even though we never touch the db
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
