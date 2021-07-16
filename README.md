## Spark Streaming

### Infrastructure

``
MySQL -> Debezium -> Kafka -> Apache Spark -> Console 
``

### Start app
[Click here to see steps](resources/steps.md)


### Use cases

#### Customer
* Simple enrichment: [customer-enrichment](pyspark/customer/customer-enrich.py)


#### Order
* Enrich order by joining with customer table:  [order-enrichment](pyspark/order/order-enrich.py)
* 1-N relationship update order when customer changed:  [1_customer-N_order](pyspark/order/1_customer-N_order.py)

