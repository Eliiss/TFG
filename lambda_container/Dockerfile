FROM public.ecr.aws/lambda/python:3.11

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --only-binary=:all: -r requirements.txt

COPY lambda_function.py .

CMD ["lambda_function.lambda_handler"]

