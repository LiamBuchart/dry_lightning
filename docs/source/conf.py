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
html_static_path = ['static']

html_theme_options = {
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

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
#import os
#import sys
#sys.path.insert(0, os.path.abspath('..'))
#sys.path.insert(0, os.path.abspath('../../'))

# copy d0.png, d1.png, and d1_yesterday.png to the _static directory
import shutil
shutil.copy('../../FORECAST/MAPS/d0.png', 'static/d0.png')
shutil.copy('../../FORECAST/MAPS/d1.png', 'static/d1.png')
shutil.copy('../../FORECAST/MAPS/d1_yesterday.png', 'static/d1_yesterday.png')
shutil.copy('../../VALIDATE/plots/validation_multipanel_last_14_days.png', 
            'static/14_timeseries.png')
shutil.copy('../../VALIDATE/plots/validation_multipanel_last_90_days.png',
            'static/90_timeseries.png')
shutil.copy('../../VALIDATE/plots/validation_mean_stats.csv', 'static/validation_mean_stats.csv')