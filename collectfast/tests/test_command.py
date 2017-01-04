from django.core.management import call_command
from django.utils.six import StringIO

from .utils import test, create_static_file


def call_collectstatic():
    out = StringIO()
    call_command('collectstatic', interactive=False, stdout=out)
    return out.getvalue()


@test
def test_basics(case):
    create_static_file('static/testfile.txt')
    result = call_collectstatic()
    case.assertIn("1 static file copied.", result)
    # file state should now be cached
    result = call_collectstatic()
    case.assertIn("0 static files copied.", result)
