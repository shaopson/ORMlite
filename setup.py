from setuptools import setup

setup(
    name='ormlite',
    version='1.0',
    description='This is a simple ORM',
    author='LingWenshao',
    author_email='shaopson@outlook.com',
    url='https://github.com/Dev-Shao/ORMlite',
    packages=['ormlite',"ormlite.fields","ormlite.db","ormlite.db.sqlite3","ormlite.db.mysql"],
    zip_safe = False,
)
