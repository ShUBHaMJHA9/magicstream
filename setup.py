import os
from setuptools import setup, find_packages

# Read README.md for long description
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Read requirements.txt
requirements = []
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [
            line.strip()
            for line in fh
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="magicstream",
    version="2.0.0",
    author="Shubham Kumar Jha",
    description="Professional 24/7 Multi-Platform Live Broadcast Engine with Adaptive Hardware Downgrading, Watermark Overlays, and Multi-Destination RTMP.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shubhamkumarjha/magicstream",
    project_urls={
        "Bug Tracker": "https://github.com/shubhamkumarjha/magicstream/issues",
        "Source Code": "https://github.com/shubhamkumarjha/magicstream",
    },
    packages=find_packages(include=["magicstream", "magicstream.*", "core", "core.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "magicstream = magicstream.cli:main",
            "magicstream-studio = magicstream.runner:main",
        ],
    },
)
