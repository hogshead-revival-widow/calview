from setuptools import setup, find_packages


setup(
    name='calview',
    version='0.0.1',
    description='Command line tool to generate formatted output based on a calendar (via CalDAV)',
    packages=find_packages(),
    package_data={'': ['data/*.py']},
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=['caldav ~= 0.7.1', 'python-dateutil ~= 2.8.1'],
    entry_points={
        "console_scripts": ["calviewer = calview.console:main"]
    }
)
