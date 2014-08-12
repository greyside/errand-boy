#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import errand_boy

package_name = 'errand_boy'
test_package_name = 'tests'

setup(
    name='errand-boy',
    version=errand_boy.__version__,
    description="Establish a connection to the errand-boy deamon to execute commands without the memory overhead incurred by os.fork().",
    author='Seán Hayes',
    author_email='sean@seanhayes.name',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    keywords='os fork process memory celery',
    url='https://github.com/SeanHayes/errand-boy',
    download_url='https://github.com/SeanHayes/errand-boy',
    license='BSD',
    packages=find_packages(),
    install_requires=['eventlet', 'six'],
    tests_require=[
        'mock',
    ],
    include_package_data=True,
    test_suite = test_package_name,
)

