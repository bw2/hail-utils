"""This Hail Batch pipeline performs the "register" step described in
https://support.terra.bio/hc/en-us/articles/7448594459931-When-and-how-to-use-a-service-account-in-Terra
It allows your Hail Batch service account to then be granted access to Terra buckets.
"""

import argparse
import hailtop.batch as hb

DOCKER_IMAGE = "broadinstitute/firecloud-tools:latest"
JOB_NAME = "register Batch service account in Terra"

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--billing-project", required=True, help="Your Hail Batch billing project.")
parser.add_argument("-t", "--tmp-bucket", required=True, help="Hail Batch temp bucket.")
parser.add_argument("-e", "--email", required=True, help="Your Hail Batch service account's email address. "
                    "To find this, go to https://batch.hail.is and click on your username in the top right.")
args = parser.parse_args()


service_backend = hb.ServiceBackend(billing_project=args.billing_project, remote_tmpdir=args.tmp_bucket)
b = hb.Batch(name=JOB_NAME, backend=service_backend)
j = b.new_job(name=JOB_NAME)
j.image(DOCKER_IMAGE)
j.command("set -x")

# rewrite the firecloud-tools version of register_service_account.py to work around https://github.com/broadinstitute/firecloud-tools/issues/46
j.command("""cat > scripts/register_service_account/register_service_account.py <<EOF
from common import *
from argparse import ArgumentParser

def main():
    # The main argument parser
    parser = ArgumentParser(description="Register a service account for use in FireCloud.")

    # Core application arguments
    parser.add_argument('-j', '--json_credentials', dest='json_credentials', action='store', required=True, help='Path to the json credentials file for this service account.')
    parser.add_argument('-e', '--owner_email', dest='owner_email', action='store', required=True, help='Email address of the person who owns this service account')
    parser.add_argument('-u', '--url', dest='fc_url', action='store', default="https://api.firecloud.org", required=False, help='Base url of FireCloud server to contact (Default Prod URL: "https://api.firecloud.org", Dev URL: "https://firecloud-orchestration.dsde-dev.broadinstitute.org")')

    # Additional arguments
    parser.add_argument('-f', '--first_name', dest='first_name', action='store', default="None", required=False, help='First name to register for user')
    parser.add_argument('-l', '--last_name', dest='last_name', action='store', default="None", required=False, help='Last name to register for user')

    args = parser.parse_args()

    from oauth2client.service_account import ServiceAccountCredentials
    scopes = ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(args.json_credentials, scopes=scopes)
    headers = {"Authorization": "bearer " + credentials.get_access_token().access_token}
    headers["User-Agent"] = firecloud_api.FISS_USER_AGENT

    uri = args.fc_url + "/register/profile"

    profile_json = {"firstName": args.first_name,
                    "lastName": args.last_name,
                    "title": "None",
                    "contactEmail": args.owner_email,
                    "institute": "None",
                    "institutionalProgram": "None",
                    "programLocationCity": "None",
                    "programLocationState": "None",
                    "programLocationCountry": "None",
                    "pi": "None",
                    "nonProfitStatus": "false"}
    request = requests.post(uri, headers=headers, json=profile_json, verify=False)

    if request.status_code == 200:
        print("The service account %s is now registered with FireCloud. You can share workspaces with this address, or use it to call APIs." % credentials._service_account_email)
    else:
        fail("Unable to register service account: %s" % request.text)

if __name__ == "__main__":
    main()
EOF""")

# run the register_service_account.py script
j.command(f"python scripts/register_service_account/register_service_account.py -j /gsa-key/key.json -e {args.email}")
b.run()
