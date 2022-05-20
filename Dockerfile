FROM ubuntu:20.04

RUN apt-get update && apt-get install -y python3 \
    && apt-get install -y python3-pip

RUN pip install python-jenkins

#define working directory
WORKDIR /ProjectJenkins

COPY jenkins_conn_log.log .
COPY my_config.ini .
COPY connection.py .

ENTRYPOINT ["python3"]

CMD ["./connection.py"]
