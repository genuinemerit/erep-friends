# coding: utf-8
"""
erepFriends

To install ErepFriends...
- cd to directory that contains setup.py
- `python3 ./setup.py sdist bdist_wheel`
If git submodules are used, then to refresh a
  submodule locally after having refreshed it in GitHub
  then in the same directory...
- `git submodule update --remote --merge`
"""
# IMPORTS
from setuptools import setup, find_packages
# CONSTANTS
NAME = "ErepFriends"
VERSION = "0.1.0"
with open('./requirements.txt', 'r') as f_req:
    REQUIRES = f_req.read()
with open('./README.md', 'r') as f_desc:
    README = f_desc.read()
# SETUP
setup(
    name=NAME,
    version=VERSION,
    author="Phoenix Quinn",
    author_email="pq_rfw@pm.me",
    description="eRepublik Citizens Data Analytics",
    long_description_content_type="text/markdown",
    long_description=README,
    url="https://github.com/genuinemerit/erep-friends.git",
    keywords=["eRepublik", "API", "ErepFriends"],
    install_requires=REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: X11 Applications",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Database",
        "Topic :: Games/Entertainment"
    ],
    python_requires='>=3.6',
)
