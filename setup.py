# based on https://uoftcoders.github.io/studyGroup/lessons/python/packages/lesson/

import os
import tempfile
from setuptools import setup
from setuptools.command.install import install
import urllib.request

from pyspark.find_spark_home import _find_spark_home

class PostInstallCommand_v1(install):
    # from https://mvnrepository.com/artifact/com.google.cloud.bigdataoss/gcs-connector/hadoop2-1.9.17
    GCS_CONNECTOR_URL = 'https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-1.9.17/gcs-connector-hadoop2-1.9.17.jar'

    def run(self):
        install.run(self)

        spark_home = _find_spark_home()

        local_jar_path = os.path.join(spark_home, "jars", os.path.basename(PostInstallCommand_v1.GCS_CONNECTOR_URL))
        try:
            self.announce("Downloading %s to %s" % (PostInstallCommand_v1.GCS_CONNECTOR_URL, local_jar_path), level=3)
            urllib.request.urlretrieve(PostInstallCommand_v1.GCS_CONNECTOR_URL, local_jar_path)
        except Exception as e:
            self.warn("Unable to download GCS connector to %s. %s" % (local_jar_path, e))
            return



class PostInstallCommand_v2(install):
    GCS_CONNECTOR_INSTALL_SCRIPT_URL = "https://raw.githubusercontent.com/hail-is/hail/master/hail/install-gcs-connector.sh"

    def run(self):
        install.run(self)

        local_script_path = os.path.join(tempfile.tempdir or "/tmp", os.path.basename(PostInstallCommand_v2.GCS_CONNECTOR_INSTALL_SCRIPT_URL))
        self.announce("Downloading %s to %s" % (PostInstallCommand_v2.GCS_CONNECTOR_INSTALL_SCRIPT_URL, local_script_path), level=3)
        urllib.request.urlretrieve(PostInstallCommand_v2.GCS_CONNECTOR_INSTALL_SCRIPT_URL, local_script_path)

        self.spawn(["chmod", "777", local_script_path])
        self.spawn([local_script_path])


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
        #'install': PostInstallCommand_v1,
        'install': PostInstallCommand_v2,
    },
)
