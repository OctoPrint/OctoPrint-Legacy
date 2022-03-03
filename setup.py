#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
from distutils.command.build_py import build_py as _build_py

import versioneer  # noqa: F401

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "src"))
import setuptools  # noqa: F401,E402

import octoprint_setuptools  # noqa: F401,E402

# ----------------------------------------------------------------------------------------

# Supported python versions
# we test against 2.7, 3.6 and 3.7, so that's what we'll mark as supported
PYTHON_REQUIRES = ">=2.7.9, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4"

# Requirements for setup.py
SETUP_REQUIRES = ["markdown==3.1.1"]  # newer versions require Python 3

# Requirements for our application
INSTALL_REQUIRES = [
    "blinker==1.4",
    "cachelib==0.1.1",
    "Click==7.1.2",
    "emoji==1.6.3",
    "filetype==1.0.9",
    "Flask-Assets==2.0",
    "Flask-Babel==1.0.0",
    "Flask-Login==0.5.0",
    "flask==1.1.4",
    "future==0.18.2",
    "itsdangerous==1.1.0",
    "Jinja2==2.11.3",
    "markdown==3.1.1",
    "markupsafe==1.1.1",
    "netaddr==0.8.0",
    "netifaces==0.11.0",
    "OctoPrint-FileCheck==2021.2.23",
    "OctoPrint-FirmwareCheck==2021.10.11",
    "OctoPrint-PiSupport==2022.3.1",
    "pkginfo==1.8.2",
    "psutil==5.9.0",
    "pylru==1.2.0",
    "pyserial==3.5",
    "PyYAML==5.4.1",
    "requests==2.27.1",
    "sarge==0.1.6",
    "semantic_version==2.8.5",
    "watchdog==0.10.4",
    "websocket-client==0.59.0",
    "werkzeug==1.0.1",
    "wrapt==1.12.1",
    "zipstream-new==1.1.8",
]

# Python 2 specific requirements
INSTALL_REQUIRES_PYTHON2 = [
    "chainmap==1.0.3",
    "colorlog==4.8.0",
    "enum34==1.1.10",
    "feedparser==5.2.1",
    "frozendict==1.2",
    "futures==3.3.0",
    "monotonic==1.6",
    "regex==2021.11.10",
    "scandir==1.10.0",
    "tornado==5.1.1",
    "typing==3.10.0.0",
    "unidecode==1.2.0",
]

# Python 3 specific requirements
INSTALL_REQUIRES_PYTHON3 = [
    "colorlog==5.0.1",
    "feedparser==6.0.8",
    "immutabledict==2.2.1",
    "pathvalidate==2.5.0",
    "regex==2022.1.18",
    "tornado==6.1",
    "unidecode==1.3.2",
    "zeroconf==0.33.4",
]

# OSX specific requirements
INSTALL_REQUIRES_OSX = [
    "appdirs==1.4.4",
]

EXTRA_REQUIRES = {}

# Dependency links for any of the aforementioned dependencies
DEPENDENCY_LINKS = []

# adapted from https://hynek.me/articles/conditional-python-dependencies/
if int(setuptools.__version__.split(".", 1)[0]) < 18:
    # no bdist_wheel support for setuptools < 18 since we build universal wheels and our optional dependencies
    # would get lost there
    assert "bdist_wheel" not in sys.argv

    # add optional dependencies for setuptools versions < 18 that don't yet support environment markers
    if sys.version_info[0] < 3:
        INSTALL_REQUIRES += INSTALL_REQUIRES_PYTHON2
    else:
        INSTALL_REQUIRES += INSTALL_REQUIRES_PYTHON3

    if sys.platform == "darwin":
        INSTALL_REQUIRES += INSTALL_REQUIRES_OSX
else:
    # environment markers supported
    EXTRA_REQUIRES[":python_version < '3'"] = INSTALL_REQUIRES_PYTHON2
    EXTRA_REQUIRES[":python_version >= '3'"] = INSTALL_REQUIRES_PYTHON3
    EXTRA_REQUIRES[":sys_platform == 'darwin'"] = INSTALL_REQUIRES_OSX

# -----------------------------------------------------------------------------------------------------------------------
# Anything below here is just command setup and general setup configuration

here = os.path.abspath(os.path.dirname(__file__))


def read_file_contents(path):
    import codecs

    with codecs.open(path, encoding="utf-8") as f:
        return f.read()


def md_to_html_build_py_factory(files, baseclass):
    class md_to_html_build_py(baseclass):
        files = {}

        def run(self):
            print("RUNNING md_to_html_build_py")
            if not self.dry_run:
                for directory, files in self.files.items():
                    target_dir = os.path.join(self.build_lib, directory)
                    self.mkpath(target_dir)

                    for entry in files:
                        if isinstance(entry, tuple):
                            if len(entry) != 2:
                                continue
                            source, dest = entry[0], os.path.join(target_dir, entry[1])
                        else:
                            source = entry
                            dest = os.path.join(target_dir, source + ".html")

                        print("Rendering markdown from {} to {}".format(source, dest))

                        from markdown import markdownFromFile

                        markdownFromFile(input=source, output=dest, encoding="utf-8")
            baseclass.run(self)

    return type(md_to_html_build_py)(
        md_to_html_build_py.__name__, (md_to_html_build_py,), {"files": files}
    )


def get_cmdclass():
    # make sure these are always available, even when run by dependabot
    global versioneer, octoprint_setuptools, md_to_html_build_py_factory

    cmdclass = versioneer.get_cmdclass()

    # add clean command
    cmdclass.update(
        {
            "clean": octoprint_setuptools.CleanCommand.for_options(
                source_folder="src", eggs=["OctoPrint*.egg-info"]
            )
        }
    )

    # add translation commands
    translation_dir = "translations"
    pot_file = os.path.join(translation_dir, "messages.pot")
    bundled_dir = os.path.join("src", "octoprint", "translations")
    cmdclass.update(
        octoprint_setuptools.get_babel_commandclasses(
            pot_file=pot_file,
            output_dir=translation_dir,
            pack_name_prefix="OctoPrint-i18n-",
            pack_path_prefix="",
            bundled_dir=bundled_dir,
        )
    )

    cmdclass["build_py"] = md_to_html_build_py_factory(
        {
            "octoprint/templates/_data": [
                "AUTHORS.md",
                "SUPPORTERS.md",
                "THIRDPARTYLICENSES.md",
            ]
        },
        cmdclass["build_py"] if "build_py" in cmdclass else _build_py,
    )

    return cmdclass


def params():
    # make sure these are always available, even when run by dependabot
    global versioneer, get_cmdclass, read_file_contents, here, PYTHON_REQUIRES, SETUP_REQUIRES, INSTALL_REQUIRES, EXTRA_REQUIRES, DEPENDENCY_LINKS

    name = "OctoPrint"
    version = versioneer.get_version()
    cmdclass = get_cmdclass()

    description = "The snappy web interface for your 3D printer"
    long_description = read_file_contents(os.path.join(here, "README.md"))
    long_description_content_type = "text/markdown"

    python_requires = PYTHON_REQUIRES
    setup_requires = SETUP_REQUIRES
    install_requires = INSTALL_REQUIRES
    extras_require = EXTRA_REQUIRES
    dependency_links = DEPENDENCY_LINKS

    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Other Audience",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Natural Language :: English",
        "Natural Language :: German",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: JavaScript",
        "Topic :: Printing",
        "Topic :: System :: Monitoring",
    ]
    author = "Gina Häußge"
    author_email = "gina@octoprint.org"
    url = "https://octoprint.org"
    license = "GNU Affero General Public License v3"
    keywords = "3dprinting 3dprinter 3d-printing 3d-printer octoprint"

    project_urls = {
        "Community Forum": "https://community.octoprint.org",
        "Bug Reports": "https://github.com/OctoPrint/OctoPrint/issues",
        "Source": "https://github.com/OctoPrint/OctoPrint",
        "Funding": "https://support.octoprint.org",
    }

    packages = setuptools.find_packages(where="src")
    package_dir = {
        "": "src",
    }
    package_data = {
        "octoprint": octoprint_setuptools.package_data_dirs(
            "src/octoprint", ["static", "templates", "plugins", "translations"]
        )
        + ["util/piptestballoon/setup.py"]
    }

    include_package_data = True
    zip_safe = False

    if os.environ.get("READTHEDOCS", None) == "True":
        # we can't tell read the docs to please perform a pip install -e .[docs], so we help
        # it a bit here by explicitly adding the development dependencies, which include our
        # documentation dependencies
        install_requires = install_requires + extras_require["docs"]

    entry_points = {"console_scripts": ["octoprint = octoprint:main"]}

    return locals()


setuptools.setup(**params())
