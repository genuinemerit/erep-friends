# coding: utf-8
"""
erep-friends

To build an efriends distribution package:
- `cd` to /dir/where/setup.py/resides
- `python3 ./setup.py sdist bdist_wheel`

To install this as a package:
`sudo -H python3 -m pip install -e /dir/where/setup.py/resides`
like...
`sudo -H python3 -m pip install -e /home/dave/Dropbox/projects/erep-friends`
(or install to your preferred python3 environment)

Then, to make the program easily executable from command line:
copy the following files to /usr/local/bin:
~/erep-friends/efriends/efriends
~/erep-friends/efriends/efriends.py

Having problems making this work, actually.
I could import the package sometimes, not all the time. Kinda weird.
Obviously I need to understand better how to package and distribute an app.

Also, on my system (native Ubuntu 20 on a Dell laptop),
  packages installed with "-e" cannot be uninstalled cleanly using pip uninstall.
Instead:
- Delete the egg file, then
- Edit the /usr/local/lib/python3.8/dist-packages/easy-install.pth file and
  remove the package from there too.

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
