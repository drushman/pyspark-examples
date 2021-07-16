from typing import cast
from pyspark.sql.functions import col, from_json
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

kafkaServer = "kafka:9092"
sparkMaster = 'spark://spark:7077'
appName = "POC-Streaming-1N"
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
           .option("subscribe", "dbserver1.inventory.customers")
           .option("startingOffsets", "earliest")
           .load())

# Define structure for event payload
# Event data schema
schema = StructType([
    StructField("payload", StructType([
        StructField("before", StructType([
            StructField("id", IntegerType(), True),
            StructField("first_name", StringType(), True),
            StructField("last_name", StringType(), True),
            StructField("email", StringType(), True)
        ]), True),
        StructField("after", StructType([
            StructField("id", IntegerType(), True),
            StructField("first_name", StringType(), True),
            StructField("last_name", StringType(), True),
            StructField("email", StringType(), True)
        ]), True)
    ]), True)
])
structuredDF = inputDF \
    .withColumn("key", inputDF["key"].cast(StringType())) \
    .withColumn("value", inputDF["value"].cast(StringType())) \
    .withColumn("value", from_json("value", schema)) \
    .select(
    col("value.payload.after.id").alias("id"),
    col("value.payload.after.first_name").alias("first_name"),
    col("value.payload.after.last_name").alias("last_name"),
    col("value.payload.after.email").alias("email"),
)

# Online enrichment
def transformRealtime(df):
    dfOrders = spark.read.format("jdbc") \
        .option("url", jdbcUrl) \
        .option("driver", "com.mysql.jdbc.Driver") \
        .option("query", "select * from orders") \
        .load()

    return df \
        .join(dfOrders, dfOrders.purchaser == df.id) \
        .select(dfOrders.order_number, df.email, df.first_name, df.last_name)

transformedDF = structuredDF.transform(transformRealtime)
transformedDF.writeStream.outputMode("append").format("console").start().awaitTermination()


# Debugging
# structuredDF.writeStream.outputMode("append").format("console").start().awaitTermination()




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

