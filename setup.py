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


# If you want to include the root sqlite3.db alongside the package,
# use data_files to install at top-level of site-packages.
# Also include any .db inside pcfg_lib (e.g. data/*.db).
setup(
    name="pcfg_lib",
    version="0.6",
    author="",
    author_email="",
    description="PCFG-based password guessing library",
    url="https://github.com/Creeper0809/PCFGCracking",
    packages=find_packages(include=["pcfg_lib", "pcfg_lib.*"]),
    include_package_data=True,
    # Include any .db files inside the pcfg_lib package
    package_data={
        "pcfg_lib": ["*.db", "data/*.db", "data/*.txt"],
    },
    install_requires=load_requirements("requirements.in"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
