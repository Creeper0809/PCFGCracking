from setuptools import setup, find_packages

def load_requirements(filename):
    with open(filename, encoding="utf-8", errors="ignore") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#") and not line.startswith("-")
        ]

setup(
    name="pcfg_lib",
    version="0.1",
    packages=find_packages(where=".", exclude=["tests*", "docs*"]),
    package_dir={"": "."},
    include_package_data=True,
    install_requires=load_requirements("requirements.in"),
)
