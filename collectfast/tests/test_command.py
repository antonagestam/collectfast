from django.core.management import call_command
from django.utils.six import StringIO

from .utils import test, create_static_file


@test
def test_command(case):
    create_static_file('static/testfile.txt')
    out = StringIO()
    call_command('collectstatic', '--no-input', stdout=out)
    result = out.getvalue()
    case.assertIn("1 static file copied.", result)
    call_command('collectstatic', '--no-input', stdout=out)
    result = out.getvalue()
    case.assertIn("0 static files copied.", result)
