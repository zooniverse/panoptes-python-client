from setuptools import setup, find_packages

setup(
    name='panoptes_client',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests',
    ],
)
