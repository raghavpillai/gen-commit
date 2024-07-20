from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="gen-commit",
    version="0.2.1",
    description="Auto-generate git commit messages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/raghavpillai/gen-commit",
    author="Raghav Pillai",
    author_email="raghav@tryspeck.com",
    license="MIT",
    packages=find_packages(),
    install_requires=["openai", "anthropic"],
    entry_points={
        "console_scripts": [
            "gencommit=src:gen_commit",
        ],
    },
)
