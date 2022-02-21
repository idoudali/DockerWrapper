# `docker_wrapper` User Guide


## Installation

First, create and activate a Python virtual environment:

=== "Linux/macOS"

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

=== "Windows"

    ```powershell
    py -m venv venv
    venv\Scripts\activate
    ```

Then install the `docker_wrapper` package:

```bash
pip install .
```

When you are actively developing the module code use the ``-e`` option to
install the project in editable mode and allow code development


```bash
pip install -e .
```
