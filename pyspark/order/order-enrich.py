from typing import cast
from pyspark.sql.functions import col, from_json
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

kafkaServer = "kafka:9092"
sparkMaster = 'spark://spark:7077'
appName = "POC-Streaming"
esUrl = "http://elastis-search:9200"
jdbcUrl = "jdbc:mysql://mysqluser:mysqlpw@mysql:3306/inventory"

# .master('local')
# .master('spark://spark:7077')
# Spark session & context
spark = (SparkSession
         .builder
         .master(sparkMaster)
         .appName(appName)
         .config("spark.jars.packages",
                 "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,org.elasticsearch:elasticsearch-hadoop:7.13.2,mysql:mysql-connector-java:8.0.25")
         .getOrCreate())

# Load data from kafka to dataframe
inputDF = (spark
           .readStream
           .format("kafka")
           .option("kafka.bootstrap.servers", kafkaServer)
           .option("subscribe", "dbserver1.inventory.orders")
           .option("startingOffsets", "earliest")
           .load())

# Define structure for event payload
# Event data schema
schema = StructType([
    StructField("payload", StructType([
        StructField("after", StructType([
            StructField("order_number", IntegerType(), True),
            StructField("purchaser", IntegerType(), True),
            StructField("order_date", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("product_id", IntegerType(), True)
        ]), True)
    ]), True)
])
structuredDF = inputDF \
    .withColumn("key", inputDF["key"].cast(StringType())) \
    .withColumn("value", inputDF["value"].cast(StringType())) \
    .withColumn("value", from_json("value", schema)) \
    .select(
    col("value.payload.after.order_number").alias("order_number"),
    col("value.payload.after.order_date").alias("order_date"),
    col("value.payload.after.purchaser").alias("purchaser"),
    col("value.payload.after.quantity").alias("quantity"),
    col("value.payload.after.product_id").alias("product_id"),
)


# # Offline enrichment
# dfUserOffline = spark.read.format("jdbc") \
#     .option("url", jdbcUrl) \
#     .option("driver","com.mysql.jdbc.Driver") \
#     .option("query", "select * from customers") \
#     .load()
# def transformOffline(df):
#     return df \
#         .join(dfUserOffline, df.purchaser == dfUserOffline.id) \
#         .select(df.order_number, df.order_date, df.quantity, df.product_id, dfUserOffline.email)
#
# transformedOfflineDF = structuredDF.transformOffline(transformOffline)
# transformedOfflineDF.writeStream.outputMode("append").format("console").start().awaitTermination()


# Online enrichment
def transformRealtime(df):
    dfUser = spark.read.format("jdbc") \
        .option("url", jdbcUrl) \
        .option("driver", "com.mysql.jdbc.Driver") \
        .option("query", "select * from customers") \
        .load()

    return df \
        .join(dfUser, df.purchaser == dfUser.id) \
        .select(df.order_number, df.order_date, df.quantity, df.product_id, dfUser.email, dfUser.first_name, dfUser.last_name)

transformedDF = structuredDF.transform(transformRealtime)
transformedDF.writeStream.outputMode("append").format("console").start().awaitTermination()

#
# structuredDF.selectExpr("CAST(id AS STRING) AS key", "to_json(struct(*)) AS value") \
#     .writeStream \
#     .format("kafka") \
#     .outputMode("append") \
#     .option("kafka.bootstrap.servers", kafkaServer) \
#     .option("topic", "enriched_customer") \
#     .option("checkpointLocation", "checkpoints") \
#     .start() \
#     .awaitTermination()

