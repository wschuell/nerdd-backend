from setuptools import find_packages, setup

setup(
    name="nerdd-backend",
    version="0.1.0",
    maintainer="Steffen Hirte",
    maintainer_email="steffen.hirte@univie.ac.at",
    packages=find_packages(),
    url="https://github.com/molinfo-vienna/nerdd-backend.git",
    long_description=open("README.md").read(),
    install_requires=[
        "fastapi~=0.103.2",
        "uvicorn[standard]~=0.23.2",
        "aiokafka~=0.8.1",
        "rethinkdb~=2.4.9",
        "stringcase~=1.2.0",
        "markdown~=3.4.3",
        "Pillow~=10.0.0",
        "xmltodict~=0.13.0",
        "munch~=4.0.0",
        "python-multipart~=0.0.6",
        "aiofiles~=23.2.1",
        # necessary for rethinkdb
        "looseversion~=1.3.0",
        # install importlib-resources and importlib-metadata for old Python versions
        "importlib-resources>=5; python_version<'3.9'",
        "importlib-metadata>=4.6; python_version<'3.10'",
    ],
    extras_require={
        "dev": [
            "mypy~=0.981",
            "black~=22.6.0",
            "ipykernel~=6.19.4",
        ],
        "test": [
            "pytest",
            "pytest-watch",
            "pytest-cov",
            "pytest-bdd",
            "pytest-mock",
            "pytest-asyncio~=0.21.1",
            # "asyncmock~=0.4.2",
            "httpx~=0.25.1",
            # necessary for testing fastapi with lifespans
            "asgi_lifespan~=2.1.0",
        ],
    },
    scripts=[],
)
