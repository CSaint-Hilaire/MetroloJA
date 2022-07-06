from setuptools import find_packages, setup


setup(
    name='metroloja_lib',
    version='0.1.0',
    author='Cadisha Saint-Hilaire',
    author_email='sainthilaire.cadisha@gmail.com',
    packages=find_packages(include=['metroloja_lib']),
    scripts=['metroloja_lib/psf_analyze.py',
             'metroloja_lib/coreg_analyze.py']
    description='metroloja_lib is a python library allowing a simplified display'
    'of MetroloJ_QC analyze result.',
    url='https://github.com/CSaint-Hilaire/MetroloJA',
    install_requires=[
        "pandas",
        "scipy==1.8.0",
        "functools==0.5",
        "PyPDF2==1.26.0",
        "tkinter",
        "alive_progress==2.4.1", 
        "plotly==5.1.0", 
        "shutil", 
        "datetime==4.5", 
        "time", 
        "pathlib", 
        "glob2==0.7",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)