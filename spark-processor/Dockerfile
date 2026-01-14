FROM apache/spark:3.3.1

USER root

# Install Python and PySpark
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    python3 -m pip install --no-cache-dir pyspark==3.3.1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
ENV PYTHONUNBUFFERED=1


COPY libs/ /opt/spark-libs/

COPY stream_app.py /app/
COPY viewer.py /app/

CMD ["/bin/bash", "-c", "/opt/spark/bin/spark-submit \
    --master spark://spark-master:7077 \
    --total-executor-cores 1 \
    --executor-memory 512m \
    --executor-cores 1 \
    --deploy-mode client \
    --driver-class-path '/opt/spark-libs/postgresql-42.6.2.jar:/opt/spark-libs/kafka-clients-2.4.1.jar:/opt/spark-libs/spark-sql-kafka-0-10_2.12-3.0.0.jar:/opt/spark-libs/commons-pool2-2.6.2.jar:/opt/spark-libs/spark-token-provider-kafka-0-10_2.12-3.0.0.jar' \
    --jars '/opt/spark-libs/spark-sql-kafka-0-10_2.12-3.0.0.jar,/opt/spark-libs/kafka-clients-2.4.1.jar,/opt/spark-libs/commons-pool2-2.6.2.jar,/opt/spark-libs/spark-token-provider-kafka-0-10_2.12-3.0.0.jar,/opt/spark-libs/postgresql-42.6.2.jar' \
    /app/stream_app.py"]