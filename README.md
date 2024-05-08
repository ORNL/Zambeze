# Zambeze

Zambeze is a distributed task orchestration system to manage science application tasks across large-scale and edge computing systems.

Report a bug using [Github Issues](https://github.com/ORNL/zambeze/issues). Feature requests, questions, and other comments can be made on the [GitHub Discussions](https://github.com/ORNL/Zambeze/discussions) page. The Zambeze developers can be reached via email at [support@zambeze.org](mailto:support@zambeze.org).

## Installation

The zambeze package can be installed in a Python environment with pip using the command shown below.

```text
pip install zambeze
```

## Usage

After installing zambeze in a Python environment, start up the zambeze agent in a terminal:

```text
zambeze start
```

Go to the examples directory in this repository and run the `imagemagick_files.py` example which also requires the [ImageMagick](https://imagemagick.org) tool.

```text
cd examples
python imagemagick_files.py
```

Stop the agent after running the example.

```text
zambeze stop
```

Use `zambeze --help` to see the available commands.

## Documentation

Documentation for the zambeze package is generated with [Sphinx](https://www.sphinx-doc.org/en/master/). View the documentation at https://docs.zambeze.org.

## Contributing

If you would like to contribute to zambeze, please see the [CONTRIBUTING.md](CONTRIBUTING.md) document.
