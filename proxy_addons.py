# mitmdump --listen-host 0.0.0.0 --listen-port 8080 --set block_global=false -s proxy_addons.py

import asyncio
from mitmproxy import http, ctx
from datetime import datetime
import base64
import json
import os
import hashlib
import random


def generate_password(username: str, seed: int) -> str:
    random.seed(seed)
    random_prefix = str(random.randint(10000, 99999))
    input_string = f"{username}:{random_prefix}"
    hashed = hashlib.sha256(input_string.encode("utf-8")).hexdigest()
    return hashed[:10]

log_file_path = "logs"

# Conditional judgment, It is recommended to set it to True, which will perform rule checks on all requests to ensure that the number of chats and completions are not counted multiple times.
conditional_judgment = True # False True

# if you want to use advanced feature, set this to True. This requires that the user must configure basic authentication
is_proxy_auth_needed = True # False True

# This value is very sensitive, please change it to a value that only you know. This is the key parameter used to calculate the password.
random_seed = 123456

# Limit access to only these users
# All users you allow to use Copilot through this proxy can be customized, and they do not need to be the same as the username used to log in to Copilot.
# This plugin will automatically generate passwords and save them in user_auth.json. As an administrator, please protect this file and tell each user their generated passwords.
allowed_usernames = [
    "satomic",
    "xuefeng",
]


# Generate passwords for allowed users and save to user_auth.json
user_auth = {username: generate_password(username, random_seed) for username in allowed_usernames}

user_auth_file_path = os.path.join("logs", "user_auth.json")
os.makedirs(os.path.dirname(user_auth_file_path), exist_ok=True)

try:
    with open(user_auth_file_path, "w", encoding='utf8') as user_auth_file:
        user_auth_file.write(json.dumps(user_auth, indent=4, ensure_ascii=False))
    ctx.log.info(f"User authentication details saved to {user_auth_file_path}")
except Exception as e:
    ctx.log.error(f"Unable to save user authentication details to file: {e}")


init_info = """
🔥🔥🔥🔥🔥🔥🔥🔥Init from here🔥🔥🔥🔥🔥🔥🔥🔥
log_file_path: %s
conditional_judgment: %s
is_proxy_auth_needed: %s
random_seed: %s
allowed_usernames:\n- %s
""" % (log_file_path, conditional_judgment, is_proxy_auth_needed, random_seed, '\n- '.join(allowed_usernames))

ctx.log.info(init_info)


class RequestTypeKeywords:
    completions = "copilot-codex/completions"
    chat = "chat/completions"

class RequestType:
    completions = "completions"
    chat = "chat"


def get_request_type(flow: http.HTTPFlow):
    # Determine type, discard if not one of the two types
    if RequestTypeKeywords.completions in flow.request.url:
        request_type = RequestType.completions
    elif RequestTypeKeywords.chat in flow.request.url:
        request_type = RequestType.chat
    else:
        request_type = None
    return request_type


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
        if isinstance(ret, str):
            ctx.log.info(f"❌ Content convert failed: {ret}")
        return ret
    
    @staticmethod
    def pretty(content):
        print(json.dumps(ContentHandler.to_dicts(content=content), indent=4, ensure_ascii=False))


class ProxyReqRspSaveToFile:
    
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.usernames = {} 
        self.usage_file_path = os.path.join(log_file_path, "usage")
        self.metrics_file_path = os.path.join(log_file_path, "metrics")
        self.current_date = datetime.utcnow().date()
        ctx.log.info("Initialized ProxyReqRspSaveToJson plugin")

    def requestheaders(self, flow: http.HTTPFlow):
        proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
        if proxy_auth:
            ctx.log.info(f"Captured Proxy-Authorization in HTTP request header: {proxy_auth}")

    def get_username_password(self, flow: http.HTTPFlow):
        proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
        if proxy_auth:
            auth_string = proxy_auth.split(" ", 1)[1]
            auth_string = base64.b64decode(auth_string).decode("utf-8")
            username = auth_string.split(":", 1)[0] if auth_string and ":" in auth_string else (auth_string if auth_string else "anonymous")
            password = auth_string.split(":", 1)[1] if auth_string and ":" in auth_string else ""
            return username, password
        return "anonymous", ""

    def http_connect(self, flow: http.HTTPFlow):
        request_type = get_request_type(flow)
        if request_type:
            # in VSCode http://username@proxy_address:port
            # in JetBrains proxy_address port username password
            proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
            if proxy_auth:
                # Because not every request will have Proxy-Authorization in the header, we need to save it in a dictionary
                username, password = self.get_username_password(flow)
                self.usernames[(flow.client_conn.address[0])] = username, password
                ctx.log.info(f"Obtained Proxy-Authorization, username: {username}")
                if is_proxy_auth_needed:
                    if username not in user_auth:
                        ctx.log.warn(f"❌ Invalid username: {username}")
                        flow.response = http.Response.make(407)
                        return
                    if user_auth[username] != password:
                        ctx.log.warn(f"❌ Invalid password {password} for user: {username}")
                        flow.response = http.Response.make(407)
                        return     
            else:
                if is_proxy_auth_needed:
                    ctx.log.warn(f"❌ Missing Proxy-Authorization in request header, url: {flow.request.url}")
                    flow.response = http.Response.make(407)
                    return

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
        request_type = get_request_type(flow)
        if not request_type:
            return

        headers_request = dict(flow.request.headers)
        headers_response = dict(flow.response.headers)
        content_request = flow.request.content.decode('utf-8').replace('\"', '"')
        content_request_dict = ContentHandler.to_dicts(content_request)
        content_response = flow.response.content.decode('utf-8').replace('\"', '"')
        content_response_list = ContentHandler.to_dicts(content_response)

        editor_version = headers_request.get('editor-version', '-').replace('/', '-')

        if conditional_judgment:
            # VSCode Conditional judgment
            if 'vscode' in editor_version.lower():
                # Determine whether it is a normal completion
                if request_type == RequestType.completions:
                    # If the completion response does not contain any text, it will be invalid.
                    has_text_in_contents_response = any([content.get('choices', [{}])[0].get('text') if isinstance(content, dict) else False for content in content_response_list])
                    if not has_text_in_contents_response:
                        ctx.log.info(f'⚠️ Skipping invalid completion response, cuz there is no text in contents_response')
                        return
                    # If the response_content_length field exists, it is not the normal completion behavior. This is based on experience gained from observing multiple jsons, not based on the design document.
                    # content_length_response = headers_response.get('content-length')
                    # if content_length_response is not None:
                    #     ctx.log.info(f'⚠️ Skipping invalid completion response, cuz content_length_response is valid: {content_length_response}')
                    #     return
                # Determine whether it is a normal chat
                else:
                    # If the stop field exists, it is not the normal chat behavior. This is based on experience gained from observing multiple jsons, not based on the design document.
                    content_stop_request = content_request_dict.get('stop')
                    if content_stop_request is not None:
                        ctx.log.info(f'⚠️ Skipping invalid chat response, cuz content_stop_request is valid: {content_stop_request}')
                        return

            # JetBrains Conditional judgment
            elif 'jetbrains' in editor_version.lower():
                if request_type == RequestType.completions:
                    has_text_in_contents_response = any([content.get('choices', [{}])[0].get('text') if isinstance(content, dict) else False for content in content_response_list])
                    if not has_text_in_contents_response:
                        ctx.log.info(f'⚠️ Skipping invalid completion response, cuz there is no text in contents_response')
                        return
                else:
                    last_role_in_messages = content_request_dict.get('messages', [{}])[-1].get('role')
                    if last_role_in_messages != 'user':
                        ctx.log.info(f'⚠️ Skipping invalid chat response, cuz last_role_in_messages is not type of `user`: {last_role_in_messages}')
                        return
                    tools_request = content_request_dict.get('tools')
                    if tools_request is not None:
                        ctx.log.info(f'⚠️ Skipping invalid chat response, cuz tools_request is valid: {tools_request}')
                        return
            else:
                ctx.log.info(f"Unknown editor: {editor_version}")


        # Add milliseconds to the timestamp
        timeconsumed = round((flow.response.timestamp_end - flow.request.timestamp_start) * 1000, 2)
        timeconsumed_str = f"{timeconsumed}ms"  
 
        # Concatenate string content
        timestamp = datetime.utcnow().isoformat()
        language = content_request_dict.get('extra', {}).get('language', 'unknown')
        vscode_machineid = headers_request.get('vscode-machineid', '-')[0:10]
        client_connect_address = flow.client_conn.address[0]
        username, password = self.usernames.get(client_connect_address, ('anonymous', ''))


        log_entry = {
            'proxy-authorization': f'{username}:{password}',
            "timestamp": timestamp,
            "proxy-time-consumed": timeconsumed_str,
            'request': {
                'url': flow.request.url,
                'method': flow.request.method,
                'headers': headers_request,
                'content': content_request_dict,
            },
            'response': {
                'status_code': flow.response.status_code,
                'headers': dict(flow.response.headers),
                'content': content_response_list,
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