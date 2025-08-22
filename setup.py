"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

import os

from setuptools import find_packages, setup

# Package metadata
AUTHOR = "Amine Soukara"
EMAIL = "AmineSoukara@gmail.com"
URL = "https://github.com/AmineSoukara/Amazon-Music"
VERSION = "1.7.6"

# Get the long description from README


def get_long_description():
    """Read the long description from README.md."""
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        print("README.md not found. Using short description.")
        return "A Python package for interacting with Amazon Music services."


# Get package requirements
def get_requirements():
    """Return list of required packages with latest versions, preferring requirements.txt if it exists."""
    default_requirements = [
        "requests>=2.32.4",
        "dotmap>=1.3.30",
        "mutagen>=1.47.0",
        "pathvalidate>=3.3.1",
        "rich>=14.0.0",
        "pyfiglet>=1.0.3",
        "setuptools>=80.9.0",
    ]

    if os.path.isfile("requirements.txt"):
        with open("requirements.txt", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    return default_requirements


setup(
    name="amazon-music",
    version=VERSION,
    description="A Python package for interacting with Amazon Music services",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    maintainer=AUTHOR,
    maintainer_email=EMAIL,
    url=URL,
    license="MIT",
    keywords=["amazon", "music", "cli", "api", "downloader", "streaming", "audio"],
    project_urls={
        "Source": URL,
        "Documentation": f"{URL}#readme",
        "Tracker": f"{URL}/issues",
        "Changelog": f"{URL}/releases",
    },
    packages=find_packages(exclude=["tests*", "docs*"]),
    package_data={
        "amz": [".amazon_music_config.json"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Utilities",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "mypy>=0.910",
            "flake8>=3.9.0",
            "twine>=3.4.0",
            "wheel>=0.36.0",
        ],
        "gui": ["customtkinter>=5.1.2"],
    },
    entry_points={
        "console_scripts": [
            "amz=amz.cli:main",
        ],
    },
    zip_safe=False,
    options={"bdist_wheel": {"universal": True}},
)
