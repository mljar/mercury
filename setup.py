import os
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8", errors="ignore") as fh:
    long_description = fh.read()

def list_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths

setup(
    name="mercury",
    version="2.3.8",
    author="MLJAR Sp. z o.o.",
    maintainer="MLJAR Sp. z o.o.",
    maintainer_email="contact@mljar.com",
    description="Turn Jupyter Notebook to Web App and share with non-technical users",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=open("mercury/requirements.txt").readlines(),
    url="https://github.com/mljar/mercury",
    packages=find_packages(),
    python_requires='>=3.8',
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11"
    ],
    entry_points={
        "console_scripts": ["mercury=mercury.mercury:main"],
    },
    package_data={"mercury": list_files("frontend-dist") + ["requirements.txt"]},
    include_package_data=True,
)
