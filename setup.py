# coding: utf-8
"""
erep-friends

To build an efriends distribution package:
- `cd` to /dir/where/setup.py/resides
- `python3 ./setup.py sdist bdist_wheel`
To install this package:
`python3 -m pip install -e /dir/where/setup.py/resides`
"""
# IMPORTS
from setuptools import setup, find_packages
# CONSTANTS
NAME = "efriends"
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
    keywords=["eRepublik", "API", "erep-friends"],
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
