import os

from setuptools import find_packages, setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as fh:
        try:
            return fh.read()
        except IOError:
            return ""


def getVersion():
    with open("version.txt") as f:
        version = f.readline()
        version = "".join(version.split())
    return version


# Get list of requirements
requirements = read("requirements.txt").splitlines()
# read the contents of your README file
long_description = read("README.md")

setup(
    name="howler-api",
    version=getVersion(),
    description="Howler - API server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CybercentreCanada/howler-api/",
    author="Howler development team",
    author_email="howler@cyber.gc.ca",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="howler alerting gc canada cse-cst cse cst cyber cccs",
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        "test": [
            "pytest",
            "retrying",
            "pyftpdlib",
            "pyopenssl",
        ],
        "dev": ["flake8", "black"],
    },
    package_data={"": ["VERSION", "howler/odm/charter.txt"]},
    include_package_data=True,
)
