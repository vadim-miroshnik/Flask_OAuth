FROM python:3.9

WORKDIR /opt/app

COPY requirements.txt requirements.txt

RUN apt-get update \
    && apt-get -y install netcat

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

ENV PATH="/opt/app:${PATH}"

EXPOSE 8000

CMD ["entrypoint.sh"]
