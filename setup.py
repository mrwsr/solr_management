from setuptools import setup, find_packages


setup(name='solr_load_generator',
      install_requires=[
          'Twisted>=16.2.0',
          'treq',
          'pysolr',
          'hypothesis'],
      packages=find_packages())
