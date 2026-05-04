Getting started
===============

This project template is designed to be installed from ``pyproject.toml``
using editable installs (``-e .``) and optional "extras".

For full details, see the "Getting started" section in ``README.md``.


1. uv (recommended)
--------------------

`uv <https://docs.astral.sh/uv/>`_ is a fast Python package manager:

.. code-block:: bash

   pip install uv   # or: brew install uv
   uv pip install -e .[dev]

   # Add optional extras as needed:
   # uv pip install -e .[dev,notebook,viz,cloud,claude]


2. pip / venv
-------------

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -e .[dev]


3. Conda
--------

.. code-block:: bash

   conda env create -f environment.yml
   conda activate your_project_name
   pip install -e .[dev]


4. Docker
---------

.. code-block:: bash

   docker build -t your_project_name:dev .
   docker run --rm -it -v "$(pwd):/app" your_project_name:dev bash


5. Pre-commit hooks (optional)
-------------------------------

.. code-block:: bash

   pre-commit install
