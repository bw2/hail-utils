
**register_hail_batch_service_account_as_terra_user.py** 

This Hail Batch pipeline registers your Hail Batch service account with Terra.   


**Command lines options:**
```
~$ python3 register_hail_batch_service_account_as_terra_user.py --help

usage: register_hail_batch_service_account_as_terra_user.py [-h] -b BILLING_PROJECT -t TMP_BUCKET -e EMAIL

optional arguments:
  -h, --help            show this help message and exit
  -b BILLING_PROJECT, --billing-project BILLING_PROJECT
                        Your Hail Batch billing project.
  -t TMP_BUCKET, --tmp-bucket TMP_BUCKET
                        Hail Batch temp bucket.
  -e EMAIL, --email EMAIL
                        Your Hail Batch service account's email address. To find this, go to https://batch.hail.is and click on your username in the top right.
```

**Example command line:**
```
# This registers the Hail Batch weisburd-wfz@hail-vdc.iam.gserviceaccount.com service account with Terra

python3 register_hail_batch_service_account_as_terra_user.py -t gs://delete-after-5days -b my-billing-project  -e weisburd-wfz@hail-vdc.iam.gserviceaccount.com
```

*NOTE: This step is required before your Hail Batch service account can be granted access to Terra buckets (as described in "[When and how to use a service account in Terra](https://support.terra.bio/hc/en-us/articles/7448594459931-When-and-how-to-use-a-service-account-in-Terra)").*

---
