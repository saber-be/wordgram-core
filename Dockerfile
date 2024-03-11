FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["sh", "-c", "if [ \"$DEBUG\" = \"true\" ]; then uvicorn app.main:app --host 0.0.0.0 --port 80 --reload --log-level debug; else uvicorn app.main:app --host 0.0.0.0 --port 80 --log-level info; fi"]
