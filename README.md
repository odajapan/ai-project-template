# your_project_name

A template repository for Python-based data science projects.

This repository is intended to be used as a GitHub template ("Use this template")
for starting new data science projects. After creating your own project from this
template, you can:

-   Rename the project (replace `your_project_name` with your project name in
    files such as `README.md`, `Makefile`, and `environment.yaml`).
-   Customize Python dependencies in `requirements.txt`.
-   Add your own data pipelines, models, and notebooks under `src/` and
    `notebooks/`.

The placeholder name `your_project_name` is used throughout this template
(including under `src/your_project_name/`). You can update it in one shot with:

```bash
./scripts/rename_project.sh my_new_project
```

## Getting started

### 1. Set up a Python environment

The recommended way is to use a virtual environment with the development requirements:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install --upgrade pip
    pip install -r requirements-dev.txt
    ```

If you prefer conda, an example environment file is provided (development environment with tests and tooling):

    ```bash
    conda env create -f environment.yaml
    conda activate your_project_name
    ```

### 2. (Optional) Install pre-commit hooks

    ```bash
    pre-commit install
    # or, if you created a conda env:
    # conda run -n your_project_name pre-commit install
    ```

### 3. (Optional) Run common project commands (see `Makefile`):

The template provides a few standard Make targets to simplify common workflows:

    ```bash
    make requirements   # Install development dependencies from requirements-dev.txt
    make data           # Run the example data pipeline (src/your_project_name/data/make_dataset.py)
    make lint           # Run flake8 over src/
    make format         # Format code with black + isort
    make typecheck      # Run mypy on src/
    make test           # Run pytest on tests/
    make check          # Run lint + tests
    make precommit      # Run pre-commit hooks against all files
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
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
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

---

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
