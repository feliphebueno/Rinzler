from os import path

from setuptools import find_packages, setup

from rinzler import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rinzler",
    version=__version__,
    long_description_content_type="text/markdown",
    description="Django-based REST API Framework",
    long_description=long_description,
    url="https://github.com/feliphebueno/Rinzler",
    author="Rinzler",
    author_email="feliphezion@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="rest, api, framework, django",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    python_requires=">=3.8",
    install_requires=["setuptools==68.2.2", "Django~=3.2", "PyYAML>=6.0.1"],
)
