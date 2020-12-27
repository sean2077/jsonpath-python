"""
Author       : zhangxianbing1
Date         : 2020-12-27 11:32:20
LastEditors  : zhangxianbing1
LastEditTime : 2020-12-27 12:42:18
Description  : 
"""
from setuptools import setup, find_packages
from jsonpath import __version__, __author__

setup(
    name="jsonpath",
    version=__version__,
    author=__author__,
    packages=find_packages(),
    python_requires=">=3.6",
    zip_safe=False,
)
