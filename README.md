# Harmonic Reordering listening test
## Installation
Create and activate virtualenv
```shell
pip install -r requirements.txt
```
## Prepare the data
1.-Download the [Million Playlist Dataset](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge)
2.-Register to [Spotify API](https://developer.spotify.com/documentation/web-api/) and obtain credentials.
3.-Run the notebook `spotify_data_preparation.ipynb`. This selects top-1000 playlists in terms of popularity of at least 20 tracks, with audio available, and downloads the audio previews to `/spotify_data/previews`.
4.-Re-compute harmonic and tempo features `spoty_hfeats.json` and `spoty_hpcps.npy`(if desired) by using the `harmonic-feat-extractor` [repository](https://github.kakaocorp.com/kakaoXmtg/harmonic-feat-extractor.git).
5.-Run the notebook `compute_harmonic_reordering.ipynb` for generating the 10 harmonic reorderings that will be evaluated.

## Build the listening test webpage
```
streamlit run app/main.py
```
We recommend to deploy the app at [https://share.streamlit.io/](https://share.streamlit.io/).

## Saving results in AWS

- Create bucket `my-bucket` in S3, take note of the region
- Create policy in IAM:
```
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
```
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
```
[default]
aws_access_key_id=XXX
aws_secret_access_key=YYY
```

To sync:
```
aws s3 sync s3://my-bucket local-path
```

## Contact

Enric Guso - @enricguso - enric.guso@upf.edu
