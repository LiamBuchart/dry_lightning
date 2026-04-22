# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'DryLightningForecast1.0'
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

html_theme = 'alabaster'
html_static_path = ['_static']

html_theme_options = {
    'analytics_id': '',
    'canonical_url': '',
    'logo_only': False,
    'display_version': True,
}

# -- Copy forecast images to _images directory --------------------------------
import os
import shutil
from pathlib import Path

def copy_forecast_images(app, config):
    """Copy forecast images from FORECAST/MAPS to docs/source/_images during build"""
    source_dir = Path(__file__).parent.parent.parent / 'FORECAST' / 'MAPS'
    dest_dir = Path(__file__).parent / '_images'
    
    if source_dir.exists():
        dest_dir.mkdir(exist_ok=True)
        for png_file in source_dir.glob('*.png'):
            dest_file = dest_dir / png_file.name
            try:
                shutil.copy2(png_file, dest_file)
            except Exception as e:
                print(f"Warning: Could not copy {png_file}: {e}")

def setup(app):
    app.connect('config-inited', copy_forecast_images)
