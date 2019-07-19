# based on https://uoftcoders.github.io/studyGroup/lessons/python/packages/lesson/

from setuptools import setup

from distutils.command.sdist import sdist as sdist_orig
from distutils.errors import DistutilsExecError
import os
import urllib.request

# from https://mvnrepository.com/artifact/com.google.cloud.bigdataoss/gcs-connector/hadoop2-1.9.17

GCS_CONNECTOR_URL = 'https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-1.9.17/gcs-connector-hadoop2-1.9.17.jar'


class sdist(sdist_orig):

    def run(self):
        print("DIRECTORY:")
        print(os.getcwd())
        print(os.path.abspath(os.getcwd()))

        try:
            urllib.request.urlretrieve(GCS_CONNECTOR_URL, '/usr/local/lib/python3.7/site-packages/pyspark/jars/gcs-connector-hadoop2-latest.jar')
        except Exception as e:
            self.warn('Unable to download GCS connector: ' + str(e))

        #try:
        #    self.spawn(['ls', '-l'], shell=True)
        #except DistutilsExecError:
        #    self.warn('listing directory failed')
        super().run()

setup(
    name='hail_utils',
    url='https://github.com/bw2/hail-utils',
    author='Ben',
    author_email='ben.weisburd@gmail.com',
    packages=['hail_utils'],
    install_requires=['hail'],
    version='0.1',
    license='MIT',
    description='Misc. hail utils',
    cmdclass={
        'sdist': sdist
    }
)
