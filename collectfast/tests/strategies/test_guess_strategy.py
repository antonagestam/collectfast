from unittest import TestCase

from collectfast.strategies.base import _BOTO3_STORAGE
from collectfast.strategies.base import _BOTO3_STRATEGY
from collectfast.strategies.base import _BOTO_STORAGE
from collectfast.strategies.base import _BOTO_STRATEGY
from collectfast.strategies.base import guess_strategy
from collectfast.tests.utils import test


@test
def test_guesses_boto_from_exact(case):
    # type: (TestCase) -> None
    case.assertEqual(guess_strategy(_BOTO_STORAGE), _BOTO_STRATEGY)


@test
def test_guesses_boto3_from_exact(case):
    # type: (TestCase) -> None
    case.assertEqual(guess_strategy(_BOTO3_STORAGE), _BOTO3_STRATEGY)


@test
def test_guesses_boto_from_subclass(case):
    # type: (TestCase) -> None
    case.assertEqual(
        guess_strategy("collectfast.tests.boto_subclass.CustomStorage"), _BOTO_STRATEGY
    )


@test
def test_guesses_boto3_from_subclass(case):
    # type: (TestCase) -> None
    case.assertEqual(
        guess_strategy("collectfast.tests.boto3_subclass.CustomStorage"),
        _BOTO3_STRATEGY,
    )
