from setuptools import setup, find_packages

setup(
    name="convlogpy",
    version="0.1.2",
    author="masterivanic",
    maintainer="masterivanic",
    description="A python logger build on top of logging base in conventionallogs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/masterivanic/python-conventionallogs",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    py_modules=["convlogpy"],
)
