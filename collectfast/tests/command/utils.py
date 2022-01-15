from io import StringIO
from typing import Any

from django.core.management import call_command
from moto import mock_s3


def call_collectstatic(*args: Any, **kwargs: Any) -> str:
    out = StringIO()
    call_command(
        "collectstatic", *args, verbosity=3, interactive=False, stdout=out, **kwargs
    )
    return out.getvalue()
