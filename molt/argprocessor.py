# encoding: utf-8
#
# Copyright (C) 2011-2012 Chris Jerdonek. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * The names of the copyright holders may not be used to endorse or promote
#   products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

"""
Provides the main sys.argv processing code, but without the try-catch.

"""

import codecs
from datetime import datetime
import logging
import os
from shutil import copytree
from StringIO import StringIO
import sys

import molt
from molt import commandline
from molt.common.error import Error
from molt.common.optionparser import UsageError
from molt import constants
from molt import defaults
from molt.dirchooser import make_output_dir, DirectoryChooser
from molt import logconfig
from molt.molter import Molter
from molt.test.harness.main import run_molt_tests


_log = logging.getLogger(__name__)

ENCODING_DEFAULT = 'utf-8'


def log_error(details, verbose):
    if verbose:
        msg = traceback.format_exc()
    else:
        msg = """\
%s
Pass %s for the stack trace.""" % (details, OPTION_VERBOSE.display(' or '))
    _log.error(msg)


def run_tests(options):
    """
    Run project tests, and return the exit status to exit with.

    """
    # Suppress the display of standard out while tests are running.
    stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        test_result = run_molt_tests(verbose=options.verbose, test_output_dir=options.output_directory)
    finally:
        sys.stdout = stdout

    return constants.EXIT_STATUS_SUCCESS if test_result.wasSuccessful() else constants.EXIT_STATUS_FAIL

def _make_output_directory(options, default_output_dir):
    output_dir = options.output_directory
    return make_output_dir(output_dir, default_output_dir)

def create_demo(options):
    output_dir = _make_output_directory(options, defaults.DEMO_OUTPUT_DIR)

    os.rmdir(output_dir)
    copytree(constants.DEMO_TEMPLATE_DIR, output_dir)
    _log.info("Created demo template directory: %s" % output_dir)

    return output_dir


def _render(options, args, chooser):
    try:
        template_dir = args[0]
    except IndexError:
        raise UsageError("Template directory argument not provided.")

    if not os.path.exists(template_dir):
        raise Error("Template directory not found: %s" % template_dir)

    config_path = options.config_path
    output_dir = _make_output_directory(options, defaults.OUTPUT_DIR)

    molter = Molter(chooser=chooser)
    molter.molt(template_dir=template_dir,
                output_dir=output_dir,
                config_path=config_path)

    return output_dir


def run_args(sys_argv, chooser=None):
    if chooser is None:
        chooser = DirectoryChooser()

    options, args = commandline.parse_args(sys_argv, chooser)

    if options.run_test_mode:
        # Do not print the result to standard out.
        return run_tests(options)

    if options.create_demo_mode:
        result = create_demo(options)
    elif options.version_mode:
        result = commandline.get_version_string()
    elif options.license_mode:
        result = commandline.get_license_string()
    else:
        result = _render(options, args, chooser)

    if result is not None:
        print result

    return constants.EXIT_STATUS_SUCCESS
