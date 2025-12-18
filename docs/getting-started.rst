Getting started
===============

This project template is designed to be installed from ``pyproject.toml``
using editable installs (``-e .``) and optional "extras".

Below is a short summary of the recommended ways to create a working
development environment. For more detail, see the "Getting started" section
in ``README.md``.


1. pip / venv (Python only)
---------------------------

Create a virtual environment and install the project plus commonly used
development extras:

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -e .[dev,notebook,viz,docs,cloud]

This installs:

* the package itself (``your_project_name`` under ``src/``)
* runtime dependencies (from ``pyproject.toml``)
* development tools and commonly used extras (``dev``, ``notebook``,
  ``viz``, ``docs``, ``cloud``)

Optionally, you can add feature-specific extras such as ``vision``,
``bigquery``, or ``dashboard``:

.. code-block:: bash

   pip install -e .[dev,vision]
   pip install -e .[dev,bigquery]
   pip install -e .[dev,dashboard]


2. Conda (minimal base, extras via pip)
--------------------------------------

If you prefer conda, an example environment file is provided to create a
minimal environment with Python and pip and install the project itself:

.. code-block:: bash

   conda env create -f environment.yml
   conda activate your_project_name

To add development tools and extras, install them with pip after activating
the environment, for example:

.. code-block:: bash

   pip install -r requirements.txt
   # or: pip install -e .[dev,notebook,viz,docs,cloud]


3. Docker (optional)
--------------------

A simple Dockerfile is provided if you prefer to work inside a container:

.. code-block:: bash

   docker build -t your_project_name:dev .
   docker run --rm -it -v "$(pwd):/app" your_project_name:dev bash

Inside the container, the project and its development dependencies plus
common data-science extras are installed via
``pip install -e .[dev,notebook,viz,docs,cloud]`` using ``pyproject.toml``.


4. Pre-commit hooks (optional)
-------------------------------

This template includes a basic ``.pre-commit-config.yaml``. After installing
the development dependencies (for example via ``pip install -r
requirements.txt`` or ``pip install -e .[dev,...]``), you can enable the
hooks with:

.. code-block:: bash

   pre-commit install

If you are using a conda environment, you can also run:

.. code-block:: bash

   conda run -n your_project_name pre-commit install
