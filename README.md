# your_project_name

A template repository for Python-based data science projects.

This template assumes **Python 3.12 or later**.

This repository is intended to be used as a GitHub template ("Use this template")
for starting new data science projects. After creating your own project from this
template, you can:

    -   Rename the project (replace `your_project_name` with your project name in
        files such as `README.md`, `Makefile`, and `environment.yml`).

-   Customize Python dependencies in `requirements.txt`.
-   Add your own data pipelines, models, and notebooks under `src/` and
    `notebooks/`.

The placeholder name `your_project_name` is used throughout this template
(including under `src/your_project_name/`). You can update it in one shot with:

```bash
./scripts/rename_project.sh my_new_project
```

## Getting started

Choose one of the following ways to set up your environment.

### 1. pip / venv (Python only)

Use a virtual environment and install the project plus development extras via
`pyproject.toml`:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
        pip install --upgrade pip
        pip install -e .[dev,notebook,viz,docs,cloud]
    ```

This installs:

-   the package itself (`your_project_name` under `src/`)
-   runtime dependencies (from `pyproject.toml`)
-   development tools and commonly used extras (`dev`, `notebook`, `viz`,
    `docs`, `cloud` extras from `pyproject.toml`)

### 2. Conda

If you prefer conda, an example environment file is provided (development
environment with tests and tooling):

    ```bash
    conda env create -f environment.yml
    conda activate your_project_name
    ```

Internally this environment file runs `pip install -e .[dev,notebook,viz,docs,cloud]`
inside the conda environment, so it matches the pip/venv setup.

### 3. Docker (optional)

A simple Dockerfile is provided if you prefer to work inside a container:

    ```bash
    docker build -t your_project_name:dev .
    docker run --rm -it -v "$(pwd):/app" your_project_name:dev bash
    ```

Inside the container, the project and its development dependencies plus common
data-science extras are installed via
`pip install -e .[dev,notebook,viz,docs,cloud]` using `pyproject.toml`.

### 4. (Optional) Install pre-commit hooks

    ```bash
    pre-commit install
    # or, if you created a conda env:
    # conda run -n your_project_name pre-commit install
    ```

### 5. (Optional) Run common project commands (see `Makefile`):

The template provides a few standard Make targets to simplify common workflows:

    ```bash
        make requirements   # Install the project in editable mode with dev + common
                           # data-science extras (from pyproject.toml)
    make data           # Run the example data pipeline (src/your_project_name/data/make_dataset.py)
    make lint           # Run flake8 over src/
    make format         # Format code with black + isort
    make typecheck      # Run mypy on src/
    make test           # Run pytest on tests/
    make check          # Run lint + tests
    make precommit      # Run pre-commit hooks against all files
    ```

After installing the package in editable mode, a small example CLI is also
available:

```bash
your_project_name hello
your_project_name hello Alice
```

## Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
        ├── pyproject.toml     <- Project metadata, dependencies, and tool configuration
    ├── requirements.txt   <- Runtime dependencies for the project (also listed in pyproject.toml)
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io

## Dependency versions and lockfiles

The canonical list of dependencies for this template lives in `pyproject.toml`.
Versions are intentionally not tightly pinned so that new projects pick up
reasonably recent releases by default.

If your team prefers fully reproducible environments, consider generating
lockfiles from `pyproject.toml`, for example using `pip-tools`:

    ```bash
    pip install pip-tools
    pip-compile \
      --extra dev \
      --extra notebook \
      --extra viz \
      --extra docs \
      --extra cloud \
      -o requirements.lock \
      pyproject.toml
    ```

or using `uv`:

    ```bash
    uv pip compile \
      --extra dev \
      --extra notebook \
      --extra viz \
      --extra docs \
      --extra cloud \
      pyproject.toml \
      -o requirements.lock
    ```

You can then commit the generated `requirements.lock` file to projects created
from this template if a lockfile-based workflow fits your organization.

---

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
