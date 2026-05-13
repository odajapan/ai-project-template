"""Sphinx configuration for your_project_name documentation."""

# -- General configuration ----------------------------------------------------

extensions: list[str] = []
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "your_project_name"
version = "0.1.0"
release = "0.1.0"
exclude_patterns = ["_build"]
pygments_style = "sphinx"

# -- HTML output --------------------------------------------------------------

html_theme = "default"
html_static_path = ["_static"]
htmlhelp_basename = "your_project_namedoc"

# -- LaTeX / manpage / texinfo output -----------------------------------------

latex_documents = [
    (
        "index",
        "your_project_name.tex",
        "your_project_name Documentation",
        "Hideto Oda",
        "manual",
    ),
]

man_pages = [
    (
        "index",
        "your_project_name",
        "your_project_name Documentation",
        ["Hideto Oda"],
        1,
    )
]

texinfo_documents = [
    (
        "index",
        "your_project_name",
        "your_project_name Documentation",
        "Hideto Oda",
        "your_project_name",
        "Python data science project template.",
        "Miscellaneous",
    ),
]
