FROM python:3.11

ARG SERVICE_NAME
WORKDIR /${SERVICE_NAME}

COPY . . 
RUN pip install --no-cache-dir -r requirements.txt
