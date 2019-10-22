from unittest import TestCase

from django.core.exceptions import ImproperlyConfigured

from collectfast.strategies.base import _BOTO3_STORAGE
from collectfast.strategies.base import _BOTO3_STRATEGY
from collectfast.strategies.base import _BOTO_STORAGE
from collectfast.strategies.base import _BOTO_STRATEGY
from collectfast.strategies.base import guess_strategy
from collectfast.tests.utils import make_test


@make_test
def test_guesses_boto_from_exact(case):
    # type: (TestCase) -> None
    case.assertEqual(guess_strategy(_BOTO_STORAGE), _BOTO_STRATEGY)


@make_test
def test_guesses_boto3_from_exact(case):
    # type: (TestCase) -> None
    case.assertEqual(guess_strategy(_BOTO3_STORAGE), _BOTO3_STRATEGY)


@make_test
def test_guesses_boto_from_subclass(case):
    # type: (TestCase) -> None
    case.assertEqual(
        guess_strategy("collectfast.tests.test_storages.boto_subclass.CustomStorage"),
        _BOTO_STRATEGY,
    )


@make_test
def test_guesses_boto3_from_subclass(case):
    # type: (TestCase) -> None
    case.assertEqual(
        guess_strategy("collectfast.tests.test_storages.boto3_subclass.CustomStorage"),
        _BOTO3_STRATEGY,
    )


@make_test
def test_raises_improperly_configured_for_unguessable_class(case):
    # type: (TestCase) -> None
    with case.assertRaises(ImproperlyConfigured):
        guess_strategy("collectfast.tests.test_storages.unguessable.UnguessableStorage")


@make_test
def test_raises_improperly_configured_for_invalid_type(case):
    # type: (TestCase) -> None
    with case.assertRaises(ImproperlyConfigured):
        guess_strategy("collectfast.tests.test_storages.unguessable.NotAType")
