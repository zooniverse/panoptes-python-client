from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='panoptes_client',
    url='https://github.com/zooniverse/panoptes-python-client',
    author='Adam McMaster / Zooniverse',
    author_email='contact@zooniverse.org',
    description=(
        'This package is the Python SDK for Panoptes, the platform behind the Zooniverse. This module is intended to allow programmatic management of projects, providing high level access to the API for common project management tasks.'
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',
    version='1.6.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.4.2,<2.29',
        'future>=0.16,<0.19',
        'python-magic>=0.4,<0.5',
        'redo>=1.7',
        'six>=1.9',
    ],
    extras_require={
        'testing': [
            'mock>=2.0,<4.1',
        ],
        'docs': [
            'sphinx',
        ],
        ':python_version == "2.7"': ['futures'],
    }
)
