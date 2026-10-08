project = "PrismSNV User Documentation"
author = "PrismSNV Team"
release = "0.1.0"
language = "en"

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.githubpages",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "substitution",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "shibuya"
html_title = "PrismSNV User Documentation"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Avoid duplicate section label warnings across pages
autosectionlabel_prefix_document = True
