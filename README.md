# Harmonic Re-ranking listening test

## Running
Create and activate virtualenv
```shell
pip install -r requirements.txt
streamlit run app/main.py
```

## Saving results in AWS

- Create bucket `my-bucket` in S3, take note of the region
- Create policy in IAM:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListObjectsInBucket",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket"
            ]
        },
        {
            "Sid": "AllObjectActions",
            "Effect": "Allow",
            "Action": "s3:*Object",
            "Resource": [
                "arn:aws:s3:::my-bucket/*"
            ]
        }
    ]
}
```
- Create user in IAM, attach policy to it, and take note of `key_id` and `access_key`
- Create `.streamlit/secrets.toml`, or manage streamlit secrets in deployment:
```toml
AWS_ACCESS_KEY_ID = 'XXX'
AWS_SECRET_ACCESS_KEY = 'YYY'
AWS_DEFAULT_REGION = 'eu-central-1'  # region
AWS_PATH = 's3://my-bucket/'
```

## Downloading results
### AWS
Download and install [AWS CLI](https://aws.amazon.com/cli/)

You can use credentials from the user that you created above, or you can create a token for the root account.
`~/.aws/credentials`:
```ini
[default]
aws_access_key_id=XXX
aws_secret_access_key=YYY
```

To sync:
```shell
aws s3 sync s3://my-bucket local-path
```
