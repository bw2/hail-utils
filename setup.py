# based on https://uoftcoders.github.io/studyGroup/lessons/python/packages/lesson/

import os
from setuptools import setup

from setuptools.command.install import install
import urllib.request


class PostInstallCommand_v1(install):
    # from https://mvnrepository.com/artifact/com.google.cloud.bigdataoss/gcs-connector/hadoop2-1.9.17
    GCS_CONNECTOR_URL = 'https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-1.9.17/gcs-connector-hadoop2-1.9.17.jar'

    def run(self):
        install.run(self)

        # try downloading and installing the GCS connector jar into the pyspark site-package
        for root, dirs, files in os.walk(self.install_base, followlinks=True):
            pyspark_jars_dir = None
            for current_dir in dirs:
                if root.endswith("pyspark") and current_dir == "jars":
                    pyspark_jars_dir = os.path.join(self.install_base, root, current_dir)
                    break

            if pyspark_jars_dir:
                break
        else:
            self.warn("pyspark not found in " + str(self.install_base) + ". Unable to install GCS connector.")
            return

        local_jar_path = os.path.join(pyspark_jars_dir, os.path.basename(PostInstallCommand_v1.GCS_CONNECTOR_URL))
        try:
            urllib.request.urlretrieve(PostInstallCommand_v1.GCS_CONNECTOR_URL, local_jar_path)
            self.announce("Installed " + PostInstallCommand_v1.GCS_CONNECTOR_URL + " to " + local_jar_path, level=3)
        except Exception as e:
            self.warn("Unable to download GCS connector to " + str(local_jar_path) + ". " + str(e))
            return


class PostInstallCommand_v2(install):
    GCS_CONNECTOR_INSTALL_SCRIPT_URL = "https://github.com/hail-is/hail/blob/master/hail/install-gcs-connector.sh"

    def run(self):
        install.run(self)

        local_script_path = os.path.basename(PostInstallCommand_v2.GCS_CONNECTOR_INSTALL_SCRIPT_URL)
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
        'install': PostInstallCommand_v2,
    },
)
