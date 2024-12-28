# based on Daniel Wang's full feature script. I just simplified it. 
# the original script also contains whitelist of requests and basic authentication.

# base on https://github.com/lichaozhao/copilot-usage/blob/master/sample.py
# mitmdump --listen-host 0.0.0.0 --listen-port 8080 --set block_global=false -s proxy_addons.py

import asyncio
from mitmproxy import http, ctx
from datetime import datetime
import base64
import json
import os

# class RequestType:
#     completions = 'completions'
    # telemetry = 'telemetry' # do not save telemetry data by default


class ContentHandler:

    @staticmethod
    def is_convertible_to_dict(string):
        try:
            eval(string)
            return True
        except Exception as e:
            # print(f"Error: {traceback.format_exc(e)}")
            return False

    @staticmethod
    def to_dicts(content):
        content = content.replace('false', 'False').replace('true', 'True').replace('null', 'None')

        # for response content
        if content.startswith("data: "):
            contents = content.split("\n\n")
            ret = []
            for data in contents:
                data = data.split("data: ")[-1].replace("\\", "").replace(" ", "")
                data = eval(data) if ContentHandler.is_convertible_to_dict(data) else data
                if data != "[DONE]":
                    ret.append(data)
        else:
            # for request content
            ret = eval(content) if ContentHandler.is_convertible_to_dict(content) else content
        return ret
    
    @staticmethod
    def pretty(content):
        print(json.dumps(ContentHandler.to_dicts(content=content), indent=4, ensure_ascii=False))


class ProxyReqRspSaveToFile:
    
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.proxy_authorizations = {} 
        self.log_file_path = "logs"
        self.usage_file_path = os.path.join(self.log_file_path, "usage")
        self.metrics_file_path = os.path.join(self.log_file_path, "metrics")
        self.current_date = datetime.utcnow().date()
        ctx.log.info("Initialized ProxyReqRspSaveToJson plugin")

    def requestheaders(self, flow: http.HTTPFlow):
        proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
        if proxy_auth:
            ctx.log.info(f"Captured Proxy-Authorization in HTTP request header: {proxy_auth}")

    def http_connect(self, flow: http.HTTPFlow):
        # in VSCode http://username@proxy_address:port
        # in JetBrains proxy_address port username password
        proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
        
        if not proxy_auth:
            ctx.log.warn("Missing Proxy-Authorization in request header")
            # Continue processing to avoid proxy errors
            # flow.response = http.Response.make(401)
            # return
        else:
            auth_type, auth_string = proxy_auth.split(" ", 1)
            decoded_auth = base64.b64decode(auth_string).decode("utf-8")
            
            ctx.log.info(f"Obtained Proxy-Authorization: {decoded_auth}")
            self.proxy_authorizations[(flow.client_conn.address[0])] = decoded_auth

    def response(self, flow: http.HTTPFlow):
        # Save request to local
        ctx.log.info(f"Processing response: {flow.request.url}")
        asyncio.ensure_future(self.save_to_file(flow))

    async def save_to_file(self, flow: http.HTTPFlow):
        # if "telemetry" not in flow.request.url:
        #     print("completions=================================: ", flow.request.url)

        self.current_date = datetime.utcnow().date()
        self.metrics_file = os.path.join(self.metrics_file_path, f'copilot-usage_{self.current_date}.json')

        # Determine type, discard if not one of the two types
        request_type = None
        if "copilot-codex/completions" in flow.request.url:
            request_type = "completions"
        elif "chat/completions" in flow.request.url:
            request_type = "chat"
        else:
            return

        client_connect_address = flow.client_conn.address[0]
        proxy_auth_info = self.proxy_authorizations.get(client_connect_address)
        username = proxy_auth_info.split(":", 1)[0] if proxy_auth_info and ":" in proxy_auth_info else (proxy_auth_info if proxy_auth_info else "anonymous")

        # Add milliseconds to the timestamp
        timeconsumed = round((flow.response.timestamp_end - flow.request.timestamp_start) * 1000, 2)
        timeconsumed_str = f"{timeconsumed}ms"  
 
        # Concatenate string content
        timestamp = datetime.utcnow().isoformat()
        content_request = flow.request.content.decode('utf-8').replace('\"', '"')
        content_response = flow.response.content.decode('utf-8').replace('\"', '"')

        headers_request = dict(flow.request.headers)
        editor_version = headers_request.get('editor-version', '-').replace('/', '-')
        vscode_machineid = headers_request.get('vscode-machineid', '-')[0:10]
        request_content_dict = ContentHandler.to_dicts(content_request)
        language = request_content_dict.get('extra', {}).get('language', 'unknown')

        log_entry = {
            'proxy-authorization': proxy_auth_info,
            "timestamp": timestamp,
            "proxy-time-consumed": timeconsumed_str,
            'request': {
                'url': flow.request.url,
                'method': flow.request.method,
                'headers': headers_request,
                'content': request_content_dict,
            },
            'response': {
                'status_code': flow.response.status_code,
                'headers': dict(flow.response.headers),
                'content': ContentHandler.to_dicts(content_response),
            }
        }

        # Create directory if it doesn't exist
        directory_path = os.path.join(self.usage_file_path, username, request_type)
        os.makedirs(directory_path, exist_ok=True)

        log_file_name = f'{directory_path}/{timestamp}_{vscode_machineid}_{client_connect_address}_{editor_version}.json'.replace(':', '-')
        
        try:
            with open(log_file_name, "w", encoding='utf8') as log_file:
                log_file.write(json.dumps(log_entry, indent=4, ensure_ascii=False))
                self.update_and_save_metrics(request_type, username, editor_version, language)
            ctx.log.info(f"Log saved {log_file_name}")
        except Exception as e:
            ctx.log.error(f"Unable to save log to file: {e}")
            return

    def update_and_save_metrics(self, request_type, username, editor_version, language):
        current_date = datetime.utcnow().date()
        if current_date != self.current_date:
            self.current_date = current_date

        # Load existing metrics if the file exists
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r", encoding='utf8') as metrics_file:
                    existing_metrics = json.load(metrics_file)
                total_chat_turns = existing_metrics.get("total_chat_turns", 0)
                total_completions_count = existing_metrics.get("total_completions_count", 0)
                aggregated_metrics = existing_metrics.get("usage", {})
            except Exception as e:
                ctx.log.error(f"Unable to load existing metrics: {e}")
                total_chat_turns = 0
                total_completions_count = 0
                aggregated_metrics = {}
        else:
            total_chat_turns = 0
            total_completions_count = 0
            aggregated_metrics = {}

        if username not in aggregated_metrics:
            aggregated_metrics[username] = {
                "chat_turns": 0,
                "completions_count": 0,
                "chat": {},
                "completions": {}
            }

        if request_type == "completions":
            if editor_version not in aggregated_metrics[username]["completions"]:
                aggregated_metrics[username]["completions"][editor_version] = {}
            if language not in aggregated_metrics[username]["completions"][editor_version]:
                aggregated_metrics[username]["completions"][editor_version][language] = 0
            aggregated_metrics[username]["completions"][editor_version][language] += 1
            aggregated_metrics[username]["completions_count"] += 1
            total_completions_count += 1
        else:
            if editor_version not in aggregated_metrics[username]["chat"]:
                aggregated_metrics[username]["chat"][editor_version] = 0
            aggregated_metrics[username]["chat"][editor_version] += 1
            aggregated_metrics[username]["chat_turns"] += 1
            total_chat_turns += 1

        metrics_summary = {
            "day": str(self.current_date),
            "total_chat_turns": total_chat_turns,
            "total_completions_count": total_completions_count,
            "usage": aggregated_metrics
        }

        # Create the metrics file if it does not exist
        os.makedirs(self.metrics_file_path, exist_ok=True)

        try:
            with open(self.metrics_file, "w", encoding='utf8') as metrics_file:
                metrics_file.write(json.dumps(metrics_summary, indent=4, ensure_ascii=False))
            ctx.log.info(f"Metrics saved {self.metrics_file}")
        except Exception as e:
            ctx.log.error(f"Unable to save metrics to file: {e}")

addons = [
    ProxyReqRspSaveToFile()
]