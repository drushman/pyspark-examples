### Start services
```
export DEBEZIUM_VERSION=1.3 && \
docker-compose up -d
```

### Start MySQL connector 
This creates a connector that stream data to kafka topic via Debezium

```
curl -i -X POST -H "Accept:application/json" -H  "Content-Type:application/json" http://localhost:8083/connectors/ -d @register-mysql.json

```


### Start streaming processing job

1. SSH to jupyter container
```
docker exec -it stream-data_jupyter_1 bash
    
```

2. Start the job
```
pyspark < ~/app/pyspark/customer/customer-enrich.py
```

3. Go to MySQL and update customer data, then you will see some magic
