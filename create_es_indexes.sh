curl -X PUT "http://localhost:9200/copilot_completions" -H 'Content-Type: application/json' -d @mapping/copilot_completions_mapping.json
curl -X PUT "http://localhost:9200/copilot_chat" -H 'Content-Type: application/json' -d @mapping/copilot_chat_mapping.json
curl -X PUT "http://localhost:9200/copilot_extension" -H 'Content-Type: application/json' -d @mapping/copilot_extension_mapping.json