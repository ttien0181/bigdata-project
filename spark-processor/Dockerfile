FROM apache/spark:3.3.1

USER root

# Install Python and required packages
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --force-reinstall \
        numpy==1.23.5 \
        pandas==1.5.3 \
        pyspark==3.3.1 \
        kafka-python==2.0.2 \
        requests==2.31.0 \
        psycopg2-binary==2.9.9 \
        sqlalchemy==2.0.23 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
ENV PYTHONUNBUFFERED=1


COPY libs/ /opt/spark-libs/

# Copy all Spark applications
COPY stream_app.py /app/
COPY batch_job.py /opt/spark-apps/
COPY serving_layer.py /opt/spark-apps/

CMD ["/bin/bash", "-c", "/opt/spark/bin/spark-submit \
    --master spark://spark-master:7077 \
    --total-executor-cores 1 \
    --executor-memory 512m \
    --executor-cores 1 \
    --deploy-mode client \
    --driver-class-path '/opt/spark-libs/postgresql-42.6.2.jar:/opt/spark-libs/kafka-clients-2.4.1.jar:/opt/spark-libs/spark-sql-kafka-0-10_2.12-3.0.0.jar:/opt/spark-libs/commons-pool2-2.6.2.jar:/opt/spark-libs/spark-token-provider-kafka-0-10_2.12-3.0.0.jar' \
    --jars '/opt/spark-libs/spark-sql-kafka-0-10_2.12-3.0.0.jar,/opt/spark-libs/kafka-clients-2.4.1.jar,/opt/spark-libs/commons-pool2-2.6.2.jar,/opt/spark-libs/spark-token-provider-kafka-0-10_2.12-3.0.0.jar,/opt/spark-libs/postgresql-42.6.2.jar' \
    /app/stream_app.py"]