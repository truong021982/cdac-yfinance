# Import the SparkSession module
from pyspark.sql import SparkSession
from pyspark import SparkContext
from pyspark.sql.functions import explode, arrays_zip, from_unixtime
from pyspark.sql.types import DateType

import os

if __name__ == '__main__':

    def app():
        # Create a SparkSession
        spark = SparkSession.builder.appName("FormatStock") \
            .config("fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID", "minio")) \
            .config("fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY", "minio123")) \
            .config("fs.s3a.endpoint", os.getenv("ENDPOINT", "http://host.docker.internal:9000")) \
            .config("fs.s3a.connection.ssl.enabled", "false") \
            .config("fs.s3a.path.style.access", "true") \
            .config("fs.s3a.attempts.maximum", "1") \
            .config("fs.s3a.connection.establish.timeout", "5000") \
            .config("fs.s3a.connection.timeout", "10000") \
            .getOrCreate()

        # Read a JSON file from an MinIO bucket using the access key, secret key, 
        # and endpoint configured above
        df = spark.read.option("header", "false") \
            .json(f"s3a://{os.getenv('SPARK_APPLICATION_ARGS')}/prices.json")

        # Explode the necessary arrays
        df_exploded = df.select("timestamp", explode("indicators.quote").alias("quote")) \
            .select("timestamp", "quote.*")

        # Zip the arrays
        df_zipped = df_exploded.select(arrays_zip("timestamp", "close", "high", "low", "open", "volume").alias("zipped"))
        df_zipped = df_zipped.select(explode("zipped")).select("col.timestamp", "col.close", "col.high", "col.low", \
                                                               "col.open", "col.volume")
        df_zipped = df_zipped.withColumn('date', from_unixtime('timestamp').cast(DateType()))

        # Store in Minio
        df_zipped.write \
            .mode("overwrite") \
            .option("header", "true") \
            .option("delimiter", ",") \
            .csv(f"s3a://{os.getenv('SPARK_APPLICATION_ARGS')}/formatted_prices")

    app()
    os.system('kill %d' % os.getpid())