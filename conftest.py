import django
import os
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')


@pytest.fixture(scope='session')
def django_db_setup():
    pass
