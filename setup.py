#!/usr/bin/env python
# coding: utf-8

"""
Standard Python setup script to support distribution-related tasks.


Releasing to PyPI
-----------------

This section contains instructions for project maintainers on how to
release a new version of this project to PyPI.

(1) Prepare the release.

Make sure the code is finalized and merged to master.  Bump the version
number in setup.py, etc.

(2) Generate the reStructuredText description for setup()'s 'long_description'
keyword argument using--

    python setup.py prep

and be sure this new version is checked in.  You must have pandoc installed
to do this step:

    http://johnmacfarlane.net/pandoc/

It helps to review this auto-generated file on GitHub as a sanity check
prior to uploading because the long description will be sent to PyPI and
appear there after publishing.

(3) Push to PyPI.  To release a new version to PyPI--

    http://pypi.python.org/pypi/molt

create a PyPI user account if you do not already have one.  The user account
will need permissions to push to PyPI.  A current "Package Index Owner"
can grant you those permissions.

When you have permissions, run the following:

    python setup.py publish

If you get an error like the following--

    Upload failed (401): You must be identified to edit package information

then add a file called .pyirc to your home directory with the following
contents:

    [server-login]
    username: <PyPI username>
    password: <PyPI password>

as described here, for example:

    http://docs.python.org/release/2.5.2/dist/pypirc.html

(4) Tag the release on GitHub.  Here are some commands for tagging.

List current tags:

    git tag -l -n3

Create an annotated tag:

    git tag -a -m "first tag" "v0.1.0"

Push a tag to GitHub:

    git push --tags cjerdonek v0.1.0

"""

import os
import shutil
import sys

from molt_setup import main as setup_lib
from molt_setup.main import ENCODING_DEFAULT, convert_md_to_rst, make_temp_path, read, write


py_version = sys.version_info

# We use setuptools/Distribute because distutils does not seem to support
# the following arguments to setUp().  Passing these arguments to
# setUp() causes a UserWarning to be displayed.
#
#  * entry_points
#  * install_requires
#
import setuptools as dist
setup = dist.setup


PACKAGE_NAME = 'molt'
# TODO: instead scrape molt/__init__.py for the version number.
VERSION = '0.1.0-alpha'  # Also change in molt/__init__.py.

FILE_ENCODING = ENCODING_DEFAULT

README_PATH = 'README.md'
HISTORY_PATH = 'HISTORY.md'
LONG_DESCRIPTION_PATH = 'setup_long_description.rst'

COMMAND_PREP = 'prep'
COMMAND_PUBLISH = 'publish'
OPTION_FORCE_2TO3 = '--force2to3'

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
)

INSTALL_REQUIRES = [
    'pystache',
    'pyyaml',
]

# TODO: decide whether to use find_packages() instead.  I'm not sure that
#   find_packages() is available with distutils, for example.
# TODO: use ".".join(parts).
PACKAGES = [
    'molt',
    'molt.commands',
    'molt.common',
    # The following packages are only for testing.
    'molt.test',
    'molt.test.common',
    'molt.test.extra',
    'molt.test.harness',
    # We exclude the following deliberately to exclude them from the build
    # and to prevent them from being installed in site-packages, for example.
    #'molt_setup',
    #'molt_setup.test',
]

DATA_DIRS = [
    ('molt', ['demo', 'test/data']),
]

DATA_FILE_GLOBS = [
    '*.json',
    '*.mustache',
    '*.py',
    '*.sh',
]


def make_description_file(target_path):
    """
    Generate the long_description needed for setup.py.

    The long description needs to be formatted as reStructuredText:

      http://docs.python.org/distutils/setupscript.html#additional-meta-data

    """
    # Comments in reST begin with two dots.
    intro_text = """\
.. This file is auto-generated by setup.py for PyPI using pandoc, so this
.. file should not be edited.  Edits should go in the source files.
"""

    convert = lambda path: convert_md_to_rst(path, __file__)

    readme_text = convert(README_PATH)
    history_text = convert(HISTORY_PATH)

    sections = [intro_text, readme_text, history_text]

    description = '\n'.join(sections)

    write(description, target_path)


def prep():
    make_description_file(LONG_DESCRIPTION_PATH)


def publish():
    """
    Publish this package to PyPI (aka "the Cheeseshop").

    """
    description_path = LONG_DESCRIPTION_PATH
    temp_path = make_temp_path(description_path)
    make_description_file(temp_path)

    if read(temp_path) != read(description_path):
        print("""\
Description file not up-to-date: %s
Run the following command and commit the changes--

    python setup.py %s
""" % (description_path, PREP_COMMAND))
        sys.exit()

    print("Description up-to-date: %s" % description_path)

    answer = raw_input("Are you sure you want to publish to PyPI (yes/no)?")

    if answer != "yes":
        exit("Aborted: nothing published")

    os.system('python setup.py sdist upload')


def parse_args(sys_argv):
    """
    Modify sys_argv in place and return whether to force use of 2to3.

    """
    should_force2to3 = False
    if len(sys_argv) > 1 and sys_argv[1] == OPTION_FORCE_2TO3:
        sys_argv.pop(1)
        should_force2to3 = True

    return should_force2to3


# The purpose of this function is to follow the guidance suggested here:
#
#   http://packages.python.org/distribute/python3.html#note-on-compatibility-with-setuptools
#
# The guidance is for better compatibility when using setuptools (e.g. with
# earlier versions of Python 2) instead of Distribute, because of new
# keyword arguments to setup() that setuptools may not recognize.
def get_extra_args(should_force2to3):
    """
    Return a dictionary of extra args to pass to setup().

    """
    extra = {}
    if py_version >= (3, ) or should_force2to3:
        # Causes 2to3 to be run during the build step.
        extra['use_2to3'] = True

    return extra


def get_long_description():
    path = LONG_DESCRIPTION_PATH
    try:
        long_description = read(path)
    except IOError:
        if not os.path.exists(path):
            raise Exception("Long-description file not found at: %s\n"
                            "  You must first run the command: %s\n"
                            "  See the docstring of this module for details." % (path, COMMAND_PREP))
        raise
    return long_description


def find_package_data():
    """
    Return the value to use for setup()'s package_data argument.

    """
    package_data = {}
    file_globs = DATA_FILE_GLOBS

    for package_name, rel_dirs in DATA_DIRS:
        paths = []
        for rel_dir in rel_dirs:
            paths += setup_lib.find_package_data(package_dir=package_name, rel_dir=rel_dir, file_globs=file_globs)

        package_data[package_name] = paths

    return package_data


def main(sys_argv):

    # TODO: use the logging module instead of printing.
    # TODO: include the following in a verbose mode.
    print("%s: using: version %s of %s" % (PACKAGE_NAME, repr(dist.__version__), repr(dist)))

    should_force2to3 = parse_args(sys_argv)

    command = sys_argv[-1]

    # TODO: eliminate needing to call sys.exit(), for example by calling
    #   a main function in an else clause.
    if command == COMMAND_PUBLISH:
        publish()
        sys.exit()
    elif command == COMMAND_PREP:
        prep()
        sys.exit()

    long_description = get_long_description()
    package_data = find_package_data()
    extra_args = get_extra_args(should_force2to3)

    # We exclude the following arguments since we are able to use a
    # corresponding Trove classifier instead:
    #
    #  * license
    #
    setup(name=PACKAGE_NAME,
          version=VERSION,
          description='Mustache project templates using Python and Groome',
          long_description=long_description,
          keywords='project template mustache pystache groome',
          author='Chris Jerdonek',
          author_email='chris.jerdonek@gmail.com',
          url='http://cjerdonek.github.com/molt/',
          install_requires=INSTALL_REQUIRES,
          packages=PACKAGES,
          package_data=package_data,
          entry_points = {
            'console_scripts': [
                'molt=molt.commands.molt:main',
            ],
          },
          classifiers = CLASSIFIERS,
          **extra_args
    )


if __name__=='__main__':
    main(sys.argv)