# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
sys.path.append(os.path.abspath('../../aacrepair'))

# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# we choose Google Style Docstring Sections (see 20 lines below)
#
# def func(arg1, arg2):
#     """Summary line.
# 
#     Extended description of function.
# 
#     Args:
#         arg1 (int): Description of arg1
#         arg2 (str): Description of arg2
# 
#     Returns:
#         bool: Description of return value
# 
#     """
#     return True

# pip install sphinx-rtd-theme
# pip install sphinxcontrib-napoleon
# Use sphinx-apidoc to build your API documentation:
# $ sphinx-apidoc -f -o docs/source   ../aacrepair
# make html

# Docstring Sections¶
# All of the following section headers are supported:
# Args (alias of Parameters)
# Arguments (alias of Parameters)
# Attention
# Attributes
# Caution
# Danger
# Error
# Example
# Examples
# Hint
# Important
# Keyword Args (alias of Keyword Arguments)
# Keyword Arguments
# Methods
# Note
# Notes
# Other Parameters
# Parameters
# Return (alias of Returns)
# Returns
# Raise (alias of Raises)
# Raises
# References
# See Also
# Tip
# Todo
# Warning
# Warnings (alias of Warning)
# Warn (alias of Warns)
# Warns
# Yield (alias of Yields)
# Yields

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'aacRepair'
copyright = '2022, René Horn'
author = 'René Horn'
# release = '2.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add napoleon to the extensions list
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',  # find cross ref
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
pygments_style = 'sphinx'

html_static_path = ['_static']
html_logo = "aac_logo.svg"
html_logo_only = True
html_display_version = False
html_css_files = [
    "css-style.css",
]
