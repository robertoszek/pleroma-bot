import setuptools
import re
from os.path import join
with open("README.md", "r") as fh:
    long_description = fh.read()

with open(join('pleroma_bot', '__init__.py')) as f:
    line = next(l for l in f if l.startswith('__version__'))
    version = re.match('__version__ = [\'"]([^\'"]+)[\'"]', line).group(1)

setuptools.setup(
    name="pleroma-bot",
    version=version,
    author="Roberto Chamorro",
    author_email='robertoszek@robertoszek.xyz',
    description="Mirror one or multiple Twitter accounts in Pleroma/Mastodon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robertoszek/pleroma-twitter-info-grabber",
    packages=['pleroma_bot'],
    classifiers=[
        'Environment :: Console',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['pleroma-bot=pleroma_bot.cli:main']
    },
    python_requires='>=3.6',
    install_requires=[
        'requests>=2.24.0',
        'PyYAML>=5.3.1',
        'requests-oauthlib>=1.3.0'
    ],
    extras_require={
        'lint': [
            'flake8',
            'flake8-quotes',
        ],
        'test': [
            'tox',
            'pytest',
            'requests-mock',
            'pytest-cov',
            'python-magic-bin ; platform_system=="Windows"'
        ],
    }
)
