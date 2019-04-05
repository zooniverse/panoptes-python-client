FROM python:3-alpine

RUN apk --no-cache add libmagic

WORKDIR /usr/src/panoptes-python-client

COPY setup.py .

RUN pip install .[testing,docs]

COPY . .

RUN pip install -U .[testing,docs]
