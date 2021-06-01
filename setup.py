from setuptools import setup, find_packages

setup(
    name='panoptes_client',
    url='https://github.com/zooniverse/panoptes-python-client',
    author='Adam McMaster',
    author_email='adam@zooniverse.org',
    version='1.4.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.4.2,<2.26',
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
