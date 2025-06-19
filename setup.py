from setuptools import setup, find_packages


def load_requirements(filename: str) -> list[str]:
    """
    Load dependencies from a requirements file, ignoring comments and options.
    """
    reqs = []
    with open(filename, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            reqs.append(line)
    return reqs

setup(
    name="pcfg_lib",
    version="0.1",
    author="",
    author_email="",
    description="PCFG-based password guessing library",
    url="https://github.com/Creeper0809/PCFGCracking",
    packages=find_packages(include=["pcfg_lib", "pcfg_lib.*"]),
    include_package_data=True,
    package_data={
        "pcfg_lib": ["*.db", "data/*.db"],
    },
    data_files=[("", ["sqlite3.db"])],
    install_requires=load_requirements("requirements.in"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
