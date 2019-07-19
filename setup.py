# based on https://uoftcoders.github.io/studyGroup/lessons/python/packages/lesson/

from setuptools import setup

from setuptools.command.install import install
import os
import urllib.request

# from https://mvnrepository.com/artifact/com.google.cloud.bigdataoss/gcs-connector/hadoop2-1.9.17

GCS_CONNECTOR_URL = 'https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-1.9.17/gcs-connector-hadoop2-1.9.17.jar'


class PostInstallCommand(install):

    def run(self):

        for root, dirs, files in os.walk(self.install_base):
            pyspark_jars_dir = [d for d in dirs if "pyspark/jars" in d]
            if pyspark_jars_dir:
                pyspark_jars_dir = pyspark_jars_dir[0]
                break
        else:
            self.warn("pyspark not found in " + str(self.install_base) + ". Unable to install GCS connector.")

        self.announce(self.install_base, level=3)

        local_jar_path = os.path.join(self.install_base, pyspark_jars_dir, os.path.basename(GCS_CONNECTOR_URL))
        try:
            urllib.request.urlretrieve(GCS_CONNECTOR_URL, local_jar_path)
        except Exception as e:
            self.warn("Unable to download GCS connector. " + str(e))

        install.run(self)

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
        'install': PostInstallCommand,
    },
)
