[![Build][build-badge]][build-link]
[![PyPI][pypi-badge]][pypi-link]
[![License: MIT][license-badge]](LICENSE)
[![Docs][docs-badge]][docs-link]
[![codecov][codecov-badge]][codecov-link]
[![Codacy Badge][codacy-badge]][codacy-link]
[![CodeFactor][codefactor-badge]][codefactor-link]

# Zambeze

## Get in Touch

The main channel to reach the Zambeze team is via the support email: 
[support@zambeze.org](mailto:support@zambeze.org).

**Bug Report / Feature Request:** our preferred channel to report a bug or request a feature is via  
Zambeze's [Github Issues Track](https://github.com/ORNL/zambeze/issues).

## Installation

Dependency installation should proceed similar to any python package.
```bash
pip install -r requirements.txt
```

## Development Environment

### Code Formatting

Zambeze's code uses [Black](https://github.com/psf/black), a PEP 8 compliant code formatter, and 
[Flake8](https://github.com/pycqa/flake8), a code style guide enforcement tool. To install the
these tools you simply need to run the following:

```bash
pip install flake8 black
```

Before _every commit_, you should run the following:

```bash
black .
flake8 .
```

If errors are reported by `flake8`, please fix them before commiting the code.

### Running Tests

There are a few dependencies that need to be installed to run the pytest, if you installed the requirements.txt file then this should be covered as well.
```bash
pip install pytest
```

From the root directory using pytest we can run:

```bash
python3 -m pytest -m unit -sv
```

Some tests should only be run from the context of the GitLab runner these can be run with:
```bash
python3 -m pytest -m gitlab_runner -sv
```

[build-badge]:         https://github.com/ORNL/zambeze/workflows/Build/badge.svg
[build-link]:          https://github.com/ORNL/zambeze/actions
[license-badge]:       https://img.shields.io/github/license/ORNL/zambeze
[codacy-badge]:        https://app.codacy.com/project/badge/Grade/6a820c5946384c3e98889e7f09a4218e
[codacy-link]:         https://www.codacy.com/gh/ORNL/zambeze/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ORNL/zambeze&amp;utm_campaign=Badge_Grade
[docs-badge]:          https://readthedocs.org/projects/zambeze/badge/?version=latest
[docs-link]:           https://zambeze.readthedocs.io/en/latest/
[pypi-badge]:          https://badge.fury.io/py/zambeze.svg
[pypi-link]:           https://pypi.org/project/zambeze/
[codecov-badge]:       https://codecov.io/gh/ORNL/zambeze/branch/main/graph/badge.svg?token=H5VS82WTRZ
[codecov-link]:        https://codecov.io/gh/ORNL/zambeze
[codefactor-badge]:    https://www.codefactor.io/repository/github/ornl/zambeze/badge
[codefactor-link]:     https://www.codefactor.io/repository/github/ornl/zambeze
