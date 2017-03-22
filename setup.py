from setuptools import setup, find_packages

setup(
    name='panoptes_client',
    url='https://github.com/zooniverse/panoptes-python-client',
    author='Adam McMaster',
    author_email='adam@zooniverse.org',
    version='0.7',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.4.2',
    ],
)
