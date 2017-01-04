from functools import wraps
import warnings

from django.core.management import call_command
from django.utils.six import StringIO

from collectfast import settings
from .utils import test, create_static_file


def override_setting(name, value):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            original = getattr(settings, name)
            setattr(settings, name, value)
            ret = fn(*args, **kwargs)
            setattr(settings, name, original)
            return ret
        return wrapper
    return decorator


def call_collectstatic(*args, **kwargs):
    out = StringIO()
    call_command(
        'collectstatic', *args, interactive=False, stdout=out, **kwargs)
    return out.getvalue()


@test
def test_basics(case):
    create_static_file('static/testfile.txt')
    result = call_collectstatic()
    case.assertIn("1 static file copied.", result)
    # file state should now be cached
    result = call_collectstatic()
    case.assertIn("0 static files copied.", result)
