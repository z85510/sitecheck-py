from setuptools import setup, find_packages

setup(
    name="agentforge",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "python-dotenv>=0.19.0",
        "pydantic>=1.8.2",
        "openai>=1.0.0",
        "anthropic>=0.5.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.2",
        "langchain-community>=0.0.10",
        "chromadb>=0.4.0",
    ],
    python_requires=">=3.8",
) 