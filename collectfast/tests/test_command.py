import warnings

from django.core.management import call_command
from django.utils.six import StringIO

from .utils import test, clean_static_dir, create_static_file, override_setting
from .utils import with_bucket


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
@override_setting("preload_metadata_enabled", False)
@with_bucket
def test_warn_preload_metadata(case):
    clean_static_dir()
    create_static_file()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        call_collectstatic()
        case.assertIn('AWS_PRELOAD_METADATA', str(w[0].message))


@test
@override_setting("file_overwrite_enabled", False)
@with_bucket
def test_warn_file_overwrite(case):
    clean_static_dir()
    create_static_file()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        call_collectstatic()
        case.assertIn('AWS_S3_FILE_OVERWRITE', str(w[0].message))


@test
@override_setting("enabled", False)
@with_bucket
def test_collectfast_disabled(case):
    clean_static_dir()
    create_static_file()
    call_collectstatic()


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
