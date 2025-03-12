curl -X POST http://localhost:3000/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-completions",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://localhost:9200",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_completions",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'


curl -X POST http://localhost:3000/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-chat",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://localhost:9200",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_chat",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'


curl -X POST http://localhost:3000/api/datasources \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GRAFANA_TOKEN" \
-d '{
  "name": "elasticsearch-extension",
  "type": "elasticsearch",
  "access": "proxy",
  "url": "http://localhost:9200",
  "basicAuth": false,
  "withCredentials": false,
  "isDefault": false,
  "jsonData": {
    "includeFrozen": false,
    "index": "copilot_extension",
    "logLevelField": "",
    "logMessageField": "",
    "maxConcurrentShardRequests": 5,
    "timeField": "day",
    "timeInterval": "1d"
  }
}'

