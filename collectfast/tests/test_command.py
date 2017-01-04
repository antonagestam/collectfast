from functools import wraps
import warnings

from django.core.management import call_command
from django.utils.six import StringIO

from collectfast import settings
from .utils import test, create_static_file, clean_static_dir


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
    clean_static_dir()
    create_static_file()
    result = call_collectstatic()
    case.assertIn("1 static file copied.", result)
    # file state should now be cached
    result = call_collectstatic()
    case.assertIn("0 static files copied.", result)


@test
@override_setting("threads", 5)
def test_threads(case):
    clean_static_dir()
    create_static_file()
    result = call_collectstatic()
    case.assertIn("1 static file copied.", result)
    # file state should now be cached
    result = call_collectstatic()
    case.assertIn("0 static files copied.", result)


@test
@override_setting("preload_metadata_enabled", False)
def test_warn_preload_metadata(case):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        call_collectstatic()
        case.assertIn('AWS_PRELOAD_METADATA', str(w[0].message))


@test
@override_setting("enabled", False)
def test_collectfast_disabled(case):
    call_collectstatic()


@test
def test_disable_collectfast(case):
    clean_static_dir()
    create_static_file()
    result = call_collectstatic(disable_collectfast=True)
    case.assertIn("1 static file copied.", result)


@test
def test_ignore_etag_deprecated(case):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        call_collectstatic(ignore_etag=True)
        case.assertIn('ignore-etag is deprecated', str(w[0].message))
