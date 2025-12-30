# AWS Lambda Python 3.12 ベースイメージ（arm64）
FROM public.ecr.aws/lambda/python:3.12-arm64

# 作業ディレクトリを設定
WORKDIR ${LAMBDA_TASK_ROOT}

# requirements.txt をコピー
COPY src/requirements.txt .

# Python 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# Lambda 関数のコードをコピー
COPY src/ .

# Lambda ハンドラーを指定
CMD ["lambda_function.handler"]
