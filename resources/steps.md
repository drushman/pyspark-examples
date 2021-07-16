### Start services
```
export DEBEZIUM_VERSION=1.3 && \
docker-compose up -d
```

### Start MySQL connector

```
curl -i -X POST -H "Accept:application/json" -H  "Content-Type:application/json" http://localhost:8083/connectors/ -d @register-mysql.json

```

