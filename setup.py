from setuptools import find_packages, setup

setup(
    name="definitions_lib",
    version="0.0.1",
    author="profcomff.com",
    author_email="admin@profcomff.com",
    description="",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license_files=["LICENSE"],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    packages=find_packages(include=["definitions"]),
    install_requires=[
        "SQLAlchemy",
        "psycopg2-binary",
        "alembic",
    ],
)
