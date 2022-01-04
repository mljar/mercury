import os
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

def list_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths

setup(
    name="mljar-mercury",
    version="0.0.1",
    maintainer="MLJAR Sp. z o.o.",
    maintainer_email="contact@mljar.com",
    description="Share your Python Notebooks with others",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=open("mercury/requirements.txt").readlines(),
    url="https://github.com/mljar/mercury",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    entry_points={
        "console_scripts": ["mercury=mercury.mercury:main"],
    },
    package_data={"mercury": list_files("frontend-dist") + ["requirements.txt"]},
    include_package_data=True,
)
