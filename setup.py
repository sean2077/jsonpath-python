from setuptools import setup, find_packages
from jsonpath import __version__, __author__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jsonpath-python",
    version=__version__,
    author=__author__,
    description="A more powerful JSONPath implementation in modern python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zhangxianbing/jsonpath-python",
    packages=find_packages("jsonpath*"),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
