#!/usr/bin/env python
# coding=utf-8

import io
import sys

import workwerobot

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex

        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


with io.open("README.md", encoding="utf8") as f:
    readme = f.read()
readme = readme.replace("latest", "v" + workwerobot.__version__)

install_requires = open("requirements.txt").readlines()
setup(
    name='WorkWeRoBot',
    version=workwerobot.__version__,
    author=workwerobot.__author__,
    author_email='2504454577@qq.com',
    url='https://github.com/pppwaw/WorkWeRoBot',
    packages=find_packages(),
    keywords="workwechat workweixin workwerobot",
    description='WeRoBot: writing WeChat Offical Account Robots with fun',
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    include_package_data=True,
    license='MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    tests_require=['pytest'],
    cmdclass={"pytest": PyTest},
    extras_require={'crypto': ["cryptography"]},
    package_data={'workwerobot': ['contrib/*.html']}
)
