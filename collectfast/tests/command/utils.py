from io import StringIO
from typing import Any

from django.core.management import call_command


def call_collectstatic(*args, **kwargs):
    # type: (Any, Any) -> str
    out = StringIO()
    call_command(
        "collectstatic", *args, verbosity=3, interactive=False, stdout=out, **kwargs
    )
    return out.getvalue()
