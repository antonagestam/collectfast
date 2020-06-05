# Changelog

## Unreleased

- Add `post_copy_hook` and `on_skip_hook` to
  `collectfast.strategies.base.Strategy`.
- Add `collectfast.strategies.filesystem.CachingFileSystemStrategy`.


## 2.1.0

- Use `concurrent.futures.ThreadPoolExecutor` instead of
  `multiprocessing.dummy.Pool` for parallel uploads.
- Support `post_process()`.

## 2.0.1

- Fix and add regression test for #178 (wrong type for `COLLECTFAST_THREADS`).
- Add tests for strictly typed settings.

## 2.0.0

- Drop support for Python 3.5.
- Drop support for Django 1.11.
- Drop support for `storages.backends.s3boto.S3BotoStorage` (remove
  `collectfast.strategies.boto.BotoStrategy`).
- Drop support for guessing strategies, e.g. require
  `COLLECTFAST_STRATEGY` to be set.
- Package type hints.
- Support django-storages 1.9+.
- Validate types of settings.

## Previous versions

For changes in previous versions see [releases on Github][releases].

[releases]: https://github.com/antonagestam/collectfast/releases
