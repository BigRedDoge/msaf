import glob
import importlib.util
from setuptools import find_packages, setup

# Load version from file
spec = importlib.util.spec_from_file_location("msaf.version", "msaf/version.py")
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)

# MSAF configuration
setup(
    name="msaf",
    version=version.version,
    description="Python module to discover the structure of music files",
    author="Oriol Nieto",
    author_email="oriol@nyu.edu",
    url="https://github.com/urinieto/msaf",
    download_url="https://github.com/urinieto/msaf/releases",
    packages=find_packages(),
    package_data={"msaf": ["algorithms/olda/models/*.npy"]},
    data_files=[
        ("msaf/algorithms/olda/models", glob.glob("msaf/algorithms/olda/models/*.npy"))
    ],
    long_description="""A python module to segment audio into all its """
    """different large-scale sections and label them based on their """
    """acoustic similarity""",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="audio music sound",
    license="MIT",
    install_requires=[
        "audioread",
        "cvxopt",
        "decorator",
        "future",
        "jams >= 0.3.0",
        "joblib",
        "librosa >= 0.6.0",
        "mir_eval",
        "matplotlib >= 1.5",
        "numpy >= 1.8.0",
        "pandas",
        "scikit-learn >= 0.17.0",
        "scipy >= 0.13.0",
        "seaborn",  # For notebook example
        "vmo >= 0.3.3",
    ],
    extras_require={
        "resample": "scikits.samplerate>=0.3",
        "tests": ["pytest", "pytest-cov"],
    },
)