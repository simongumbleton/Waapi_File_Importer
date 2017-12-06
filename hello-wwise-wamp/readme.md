# Hello Wwise Wamp - Python Sample
## Overview

This sample demonstrates how to connect to Wwise through WAAPI using Python with Autobahn and Twisted.

## Requirements

### Native packages
1. [Python 2.7.13|https://www.python.org/downloads/release/python-2713/)
2. [Microsoft Visual C++ Compiler for Python 2.7](https://www.microsoft.com/en-us/download/details.aspx?id=44266)

### Python packages
Make sure you have pip installed (it should be provided with the Python installation and the command might not be available until you restart your computer).

NB.: Prior to installing dependencies, update setuptools to allow to make use of automatic use of compiler:
	pip install --upgrade setuptools

Use ``` pip install [package_name] ```

1. pypiwin32
2. autobahn[twisted]==0.10.4

## Execution

Run the following commands from the "hello-wwise-wamp" directory:

    python main.py
