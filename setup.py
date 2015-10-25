from distutils.core import setup
from setuptools import find_packages

setup(
    name='docker-builder',
    version='0.0.0',
    author='Darwin Monroy',
    author_email='contact@darwinmonroy.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/dmonroy/docker-builder',
    install_requires=[
        'pyyaml',
        'docker-py'
    ],
    description='Build docker images from python',
)
