from setuptools import find_packages, setup

setup(
    name='qualprep',
    packages=find_packages(include=['qualprep']),
    version='0.1.1',
    description='Python library to prepare data',
    author='Lena Berger',
    license='MIT',
    install_requires=['pandas', 'numpy', 'tqdm'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)