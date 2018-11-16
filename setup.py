#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014, 2015, 2016, 2017, 2018 Martin Raspaud

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Setup for pps-runner.
"""
from setuptools import setup
import imp


version = imp.load_source(
    'nwcsafpps_runner.version', 'nwcsafpps_runner/version.py')

setup(name="pps_runner",
      version=version.__version__,
      description='Pytroll runner for PPS',
      author='Adam Dybroe',
      author_email='adam.dybroe@smhi.se',
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 " +
                   "or later (GPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering"],
      url="https://github.com/pytroll/pytroll-pps-runner",
      packages=['nwcsafpps_runner', ],
      scripts=['nwcsafpps_runner/pps_runner.py',
               'nwcsafpps_runner/pps2018_runner.py',
               'bin/pps_run.sh', ],
      data_files=[],
      zip_safe=False,
      install_requires=['posttroll', 'multiprocessing_logging'],
      # test_requires=['mock'],
      # test_suite='pps_runner.tests.suite',
      )
