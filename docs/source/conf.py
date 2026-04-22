# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'DryLightningForecast'
copyright = '2026, BuchartLiam'
author = 'BuchartLiam'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

html_theme_options = {
    'analytics_id': '',
    'canonical_url': '',
    'logo_only': False,
    'display_version': True,
    'sidebar_hide_name': False,
    'navigation_with_keys': True,
    'announcement': '',
    'light_css_variables': {
        'color-brand-primary': '#0969da',
        'color-brand-content': '#0969da',
        'font-stack': '"Segoe UI", "Helvetica Neue", sans-serif',
        'font-stack--monospace': '"SFMono-Regular", "Courier New", monospace',
    },
    'dark_css_variables': {
        'color-brand-primary': '#58a6ff',
        'color-brand-content': '#58a6ff',
    },
}
