import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.abspath('D:\\SENIC\\CV4EM-package'))
sys.path.append(os.path.abspath('D:\\SENIC\\CV4EM-package\\v0_0_1\\data'))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

release = 'v0_0_1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
     'sphinx.ext.autodoc',  
     'sphinx.ext.viewcode',
     'sphinx.ext.napoleon',
     'sphinx_autodoc_typehints',
     'IPython.sphinxext.ipython_directive',  # Needed in basic_usage.rst
     'numpydoc',
     'sphinx_design',
     'sphinx.ext.autosummary',
     'sphinx.ext.doctest',
     'sphinx.ext.githubpages',
     'sphinx.ext.mathjax',
     'sphinx.ext.inheritance_diagram',
     'sphinx.ext.intersphinx',
     'sphinx_copybutton',
     'sphinx_favicon',
]


try:
    import sphinxcontrib.spelling  # noqa: F401

    extensions.append("sphinxcontrib.spelling")
except BaseException:
    pass

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True  
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True

napoleon_include_init_with_doc = False

# Show full module path in signatures
add_module_names = False

# Display types inline with descriptions
autodoc_typehints = "description" 




templates_path = ['_templates']


autosummary_generate = True
source_suffix = ".rst"


exclude_patterns = []

numpydoc_show_class_members = False
numpydoc_xref_param_type = True
numpydoc_xref_ignore = {
    "type",
    "optional",
    "default",
    "of",
    "or",
    "auto",
    "from_elements",
    "all_alpha",
    "subclass",
    "dask",
    "scheduler",
    "matplotlib",
    "color",
    "line",
    "style",
    "widget",
    "strategy",
    "module",
    "prettytable",
}

autoclass_content = "both"

autodoc_default_options = {
    "show-inheritance": True,
}
toc_object_entries_show_parents = "hide"
numpydoc_class_members_toctree = False



project = "CV4EM"
copyright = f"2024-{datetime.today().year}, The CV4EM development team"

pygments_style = "sphinx"


html_theme_options = {
    "analytics": {
        "google_analytics_id": "G-B0XD0GTW1M",
    },
    "show_toc_level": 2,
    "github_url": "https://github.com/iceaiai/CV4EM-package",
    "icon_links": [
        {
            "name": "CV4EM",
            "url": "https://sites.gatech.edu/cv4em/2025/01/10/hello-world/",
            "icon": "_static/hyperspy.ico",
            "type": "local",
        },
    ],
    "logo": {
        "text": "CV4EM",
    },
    "external_links": [
        {
            "url": "https://github.com/iceaiai/CV4EM-package",
            "name": "Tutorial",
        },
    ],
}



copybutton_prompt_text = r">>> |\.\.\. "
copybutton_prompt_is_regexp = True

tls_verify = True


def setup(app):
    app.add_css_file("custom-styles.css")





# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
