FROM public.ecr.aws/lambda/python:3.13

# Lambdaハンドラーとモジュールをコピー
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY download_s3.py ${LAMBDA_TASK_ROOT}
COPY analyze_geojson.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# 必要な外部ライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# Lambdaのエントリーポイント
CMD ["lambda_function.lambda_handler"]