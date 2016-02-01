import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pygd2",
    version = "0.3.1",
    author = "Drew Troxell",
    author_email = "troxellus@gmail.com",
    description = ("Simple library for querying MLB's GD2 data."),
    license = "GPLv3",
    keywords = "mlb gameday stats library",
    url = "http://github.com/DrewTroxell/PyGD2",
    install_requires([
        "beautifulsoup4",
        "requests"
    ])
    packages=find_packages(),
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPLv3",
    ],
)