"""Setup configuration for SentinelZero."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    # Filter out development dependencies
    requirements = [req for req in requirements if not any(dev in req for dev in ["pytest", "black", "isort", "mypy", "pre-commit"])]

setup(
    name="sentinel-zero",
    version="0.1.0",
    author="SentinelZero Team",
    description="A macOS service that starts, monitors, schedules, and automatically restarts command-line processes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ShuhaoZQGG/sentinel-zero",
    packages=find_packages(),
    package_dir={},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "sentinel-zero=src.cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)