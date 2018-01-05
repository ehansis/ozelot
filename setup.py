from setuptools import setup

setup(name='ozelot',
      version='0.2.3',
      description='A package for building maintanable ETL pipelines',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'Topic :: Scientific/Engineering :: Information Analysis',
      ],
      keywords='data analytics ETL',
      url='https://github.com/trycs/ozelot',
      author='Eberhard Hansis',
      author_email='contact@transparent-analytics.de',
      license='MIT',
      packages=['ozelot',
                'ozelot.orm',
                'ozelot.etl'],
      install_requires=[
          'pandas>=0.17.0',
          'sqlalchemy>=1.0.0',
          'luigi>=2.2.0',
          'lxml',
          'keyring',
          'requests',
          'sadisplay',
          'future',
      ],
      test_suite='nose.collector',
      tests_require=['nose',
                     'coverage',
                     'lxml'],
      include_package_data=True,
      zip_safe=False)
