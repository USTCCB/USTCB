from pathlib import Path

from setuptools import setup, find_packages


BASE_DIR = Path(__file__).resolve().parent
readme_path = BASE_DIR / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""


setup(
    name="ustcb",
    version="0.1.0",
    author="USTCB Project",
    author_email="2403148578@qq.com",
    description="USTCB - A股财经新闻日报：每天自动抓取主要财经网站RSS新闻并通过邮件发送到QQ邮箱。",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/你的用户名/USTCB",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
)