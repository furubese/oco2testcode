import base64
import boto3
import json
import requests
import os


def retrieve_credentials(event):
    """Earthdata Loginを通してGESDISCの一時S3認証情報を取得"""
    login_resp = requests.get(event['s3_endpoint'], allow_redirects=False)
    login_resp.raise_for_status()

    # 認証情報をBase64エンコード
    auth = f"{event['edl_username']}:{event['edl_password']}"
    encoded_auth = base64.b64encode(auth.encode('ascii')).decode('ascii')

    auth_redirect = requests.post(
        login_resp.headers['location'],
        data={"credentials": encoded_auth},
        headers={"Origin": event['s3_endpoint']},
        allow_redirects=False
    )
    auth_redirect.raise_for_status()

    final = requests.get(auth_redirect.headers['location'], allow_redirects=False)
    results = requests.get(
        event['s3_endpoint'],
        cookies={'accessToken': final.cookies['accessToken']}
    )
    results.raise_for_status()

    return json.loads(results.content)


def lambda_handler(event, context):
    """GESDISCのS3から指定prefix以下をすべて/tmpにダウンロード"""
    creds = retrieve_credentials(event)

    source_bucket = event['bucket_name']
    prefix = event.get('prefix', 'OCO3_DATA/OCO3_L2_Lite_FP.11r')

    # 認証付きS3クライアント
    s3_client = boto3.client(
        's3',
        aws_access_key_id=creds["accessKeyId"],
        aws_secret_access_key=creds["secretAccessKey"],
        aws_session_token=creds["sessionToken"]
    )

    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=source_bucket, Prefix=prefix)

    downloaded_files = []

    for page in page_iterator:
        if "Contents" not in page:
            continue

        for obj in page["Contents"]:
            key = obj["Key"]
            filename = os.path.basename(key)

            # ディレクトリが空（prefixフォルダ自体など）はスキップ
            if not filename:
                continue

            tmp_path = f"/tmp/{filename}"

            # ファイルが既に存在する場合はダウンロードをスキップ
            if os.path.exists(tmp_path):
                print(f"File already exists, skipping download: {tmp_path}")
                downloaded_files.append(tmp_path)
                continue

            print(f"Downloading: {key} -> {tmp_path}")

            # 署名付きURL生成
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': source_bucket, 'Key': key},
                ExpiresIn=3600
            )

            # ダウンロード実行
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            downloaded_files.append(tmp_path)

    return {
        "statusCode": 200,
        "downloaded_files": downloaded_files
    }
