FROM alpine:latest

RUN apk update ; \
    apk add python3 py3-pip ; \
    apk add build-base python3-dev ; \
    mkdir -p /app/lib

COPY run.py requirements.txt /app/
COPY lib/* /app/lib

RUN pip install -r /app/requirements.txt

EXPOSE 9185

COPY . .

ENTRYPOINT ["/app/run.py"]