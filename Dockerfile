FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./cl.pkl /code/cl.pkl

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
