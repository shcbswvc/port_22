from setuptools import setup, find_packages

setup(
    name="scroll_breaker",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "google-generativeai",
        "requests",
    ],
)
