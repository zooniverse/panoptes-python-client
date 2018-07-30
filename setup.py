from setuptools import setup, find_packages

setup(
    name='panoptes_client',
    url='https://github.com/zooniverse/panoptes-python-client',
    author='Adam McMaster',
    author_email='adam@zooniverse.org',
    version='1.0.3',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.4.2,<2.19',
        'future>=0.16,<0.17',
        'python-magic>=0.4,<0.5',
    ],
    extras_require={
        'testing': [
            'mock>=2.0,<2.1',
        ],
        'docs': [
            'sphinx',
        ]
    }
)
