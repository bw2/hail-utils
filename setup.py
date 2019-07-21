# based on https://uoftcoders.github.io/studyGroup/lessons/python/packages/lesson/
import glob
import os
from setuptools import setup
from setuptools.command.install import install
import urllib.request

from pyspark.find_spark_home import _find_spark_home

GCS_CONNECTOR_URL = 'https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-1.9.17/gcs-connector-hadoop2-1.9.17.jar'
GENERIC_KEY_FILE_URL = 'https://raw.githubusercontent.com/macarthur-lab/seqr/master/deploy/secrets/shared/gcloud/service-account-key.json'

class PostInstallCommand(install):
    # from https://mvnrepository.com/artifact/com.google.cloud.bigdataoss/gcs-connector/hadoop2-1.9.17

    def run(self):
        install.run(self)

        spark_home = _find_spark_home()

        # download GCS connector jar
        local_jar_path = os.path.join(spark_home, "jars", os.path.basename(GCS_CONNECTOR_URL))
        try:
            self.announce("Downloading %s to %s" % (GCS_CONNECTOR_URL, local_jar_path), level=3)
            urllib.request.urlretrieve(GCS_CONNECTOR_URL, local_jar_path)
        except Exception as e:
            self.warn("Unable to download GCS connector to %s. %s" % (local_jar_path, e))
            return

        # look for existing key files in the ~/.config. If there's more than one, select the newest.
        try:
            key_file_regexp = "~/.config/gcloud/legacy_credentials/*/adc.json"
            key_file_sort = lambda file_path: -1 * os.path.getctime(file_path)
            key_file_path = next(iter(sorted(glob.glob(os.path.expanduser(key_file_regexp)), key=key_file_sort)))
            self.announce("Using key file: %s" % key_file_path, level=3)
        except Exception as e:
            self.warn("No keys found in %s. %s" % (key_file_regexp, e))
            key_file_path = None

        # download key file
        if key_file_path is None:
            local_key_dir = os.path.expanduser("~/.hail/gcs-keys")
            try:
                if not os.path.exists(local_key_dir):
                    os.makedirs(local_key_dir)
            except Exception as e:
                self.warn("Unable to create directory %s. %s" % (local_key_dir, e))
                return

            key_file_path = os.path.join(local_key_dir, "gcs-connector-key.json")
            try:
                self.announce("Downloading %s to %s" % (GENERIC_KEY_FILE_URL, key_file_path), level=3)
                urllib.request.urlretrieve(GENERIC_KEY_FILE_URL, key_file_path)
            except Exception as e:
                self.warn("Unable to download shared key from %s to %s. %s" % (GENERIC_KEY_FILE_URL, key_file_path, e))
                return

        # update spark-defaults.conf
        spark_config_file_path = os.path.join(spark_home, "conf/spark-defaults.conf")
        self.announce("Setting json.keyfile to %s in %s" % (key_file_path, spark_config_file_path), level=3)

        spark_config_lines = [
            "spark.hadoop.google.cloud.auth.service.account.enable true",
            "spark.hadoop.google.cloud.auth.service.account.json.keyfile %s" % key_file_path,
        ]
        try:
            if os.path.isfile(spark_config_file_path):
                with open(spark_config_file_path, "rt") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if "spark.hadoop.google.cloud.auth.service.account.enable" in line:
                            continue
                        if "spark.hadoop.google.cloud.auth.service.account.json.keyfile" in line:
                            continue

                        spark_config_lines.append(line)

            with open(spark_config_file_path, "wt") as f:
                for line in spark_config_lines:
                    f.write(line + "\n")

        except Exception as e:
            self.warn("Unable to update spark config %s. %s" % (spark_config_file_path, e))
            return

        #self.spawn(["chmod", "777", local_script_path])


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
