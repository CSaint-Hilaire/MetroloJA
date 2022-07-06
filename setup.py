from setuptools import find_packages, setup


setup(
    name='metroloja_lib',
    version='0.1.0',
    author='Cadisha Saint-Hilaire',
    author_email='sainthilaire.cadisha@gmail.com',
    packages=find_packages(include=['metroloja_lib']),
    scripts=['psf_analyze.py']
    description='metroloja_lib is a python library allowing a simplified display'
    'of MetroloJ_QC analyze result.',
    url='https://github.com/CSaint-Hilaire/MetroloJA/tree/main/metroloja_lib',
    install_requires=[
        "pandas",
        "scipy",
        "functools",
        "PyPDF2",
        "tkinter",
        "alive_progress", 
        "plotly.express", 
        "plotly.graph_objects", 
        "shutil", 
        "datetime", 
        "time", 
        "pathlib", 
        "glob",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)