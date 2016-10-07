#!/usr/bin/env python
from sys import version_info
from setuptools import setup, find_packages


INSTALL_REQUIRES = []

py_vers_tag = '-%s.%s' % version_info[:2]


def main():
    setup(
        name="pyteensy",
        version="0.1",
        url="https://github.com/CatherineH/teensy-python-makefile",
        author="Catherine Holloway",
        entry_points={'console_scripts': [
            'pyteensy = src:compile_upload',
            'pyteensy%s = src:compile_upload' % py_vers_tag,
            ]},
        author_email="milankie@gmail.com",
        packages=find_packages(),
        description="Catherine Holloway's teensy compilation and upload "
                    "scripts.",
        install_requires=INSTALL_REQUIRES,
        zip_safe=True
    )

if __name__ == "__main__":
    main()