import warnings

from django.core.management import call_command
from django.utils.six import StringIO
from django.test import override_settings as override_django_settings

from .utils import test, clean_static_dir, create_static_file, override_setting
from .utils import with_bucket, override_storage_attr


def call_collectstatic(*args, **kwargs):
    out = StringIO()
    call_command(
        'collectstatic', *args, interactive=False, stdout=out, **kwargs)
    return out.getvalue()


@test
@with_bucket
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
@with_bucket
def test_threads(case):
    clean_static_dir()
    create_static_file()
    result = call_collectstatic()
    case.assertIn("1 static file copied.", result)
    # file state should now be cached
    result = call_collectstatic()
    case.assertIn("0 static files copied.", result)


@test
@with_bucket
@override_django_settings(
    STATICFILES_STORAGE="collectfast.tests.no_preload_metadata.NPM")
def test_warn_preload_metadata(case):
    clean_static_dir()
    create_static_file()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        call_collectstatic()
        case.assertIn('AWS_PRELOAD_METADATA', str(w[0].message))


@test
@with_bucket
def test_collectfast_disabled(case):
    clean_static_dir()
    create_static_file()
    result = call_collectstatic(disable_collectfast=True)
    case.assertIn("1 static file copied.", result)


@test
@override_django_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
def test_collectfast_disabled_default_storage(case):
    clean_static_dir()
    create_static_file()
    result = call_collectstatic(disable_collectfast=True)
    case.assertIn("1 static file copied.", result)


@test
@with_bucket
def test_disable_collectfast(case):
    clean_static_dir()
    create_static_file()
    result = call_collectstatic(disable_collectfast=True)
    case.assertIn("1 static file copied.", result)


@test
@with_bucket
def test_ignore_etag_deprecated(case):
    clean_static_dir()
    create_static_file()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        call_collectstatic(ignore_etag=True)
        case.assertIn('ignore-etag is deprecated', str(w[0].message))


@test
@override_storage_attr("gzip", True)
@override_setting("is_gzipped", True)
@with_bucket
def test_is_gzipped(case):
    clean_static_dir()
    create_static_file()
    result = call_collectstatic()
    case.assertIn("1 static file copied.", result)
    # file state should now be cached
    result = call_collectstatic()
    case.assertIn("0 static files copied.", result)
