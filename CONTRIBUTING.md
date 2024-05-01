# Contributing

Please follow the guidelines discussed on this page to contribute to the zambeze project.

## Virtual environment

Before contributing to zambeze, clone this repository and create a conda virtual environment using the `environment.yml` file. This environment contains all the dependencies needed to run and develop zambeze. Commands for creating and activating the environment are given in the environment file and also listed below.

```text
conda env create --file environment.yml
conda activate zambeze
```

## Pull requests

Code contributions should be made via pull requests to the `main` branch in the zambeze repository. Steps to submit a pull request are:

1. Create a feature branch from the `main` branch
2. Make your contributions in the feature branch
3. Adhere to the code style and format discussed below using ruff
4. Write unit tests for new code and make sure existing tests pass
5. Write documentation for new code and edit existing documentation where applicable
5. Create a pull request on GitHub when your changes are ready for review

All pull requests must pass linter checks, formatter checks, and unit tests before they can be merged with the `main` branch. See the sections below for more information about code style, formatting, testing, and documentation.

## Code style and format

Contributors should adhere to the [PEP 8 Style Guide](https://pep8.org) for Python naming conventions and code layout. Style conventions and code format are checked with the [ruff](https://github.com/astral-sh/ruff) linter and code formatter. Many editors and IDEs support ruff via plugins or extensions. Use the commands shown below to run the linter and formatter checks in the terminal:

```text
cd zambeze
ruff check .
ruff format --check .
```

These checks are utilized in the GitHub Actions workflow `checks.yml` and must pass for pull requests before merging with the `main` branch.

## Unit tests

The [pytest](https://github.com/pytest-dev/pytest) framework is used for unit testing the zambeze project. Several markers are listed in the `pyproject.toml` to run certain tests. For example, run all the unit tests with `pytest -m unit`. The GitHub Actions workflow `tests.yml` will run the tests and upload a coverage report.

## Documentation

Documentation for zambeze is generated with the [Sphinx](https://www.sphinx-doc.org/en/master/) tool. All documentation files are located in the `docs` directory. Docstrings in the Python code should use the [Numpy style and format](https://numpydoc.readthedocs.io/en/latest/format.html). The docstrings are automatically rendered by Sphinx when generating the documentation.
