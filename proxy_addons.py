# repo: https://github.com/satomic/copilot-proxy-insight-of-every-user
# version: 1.6
# mitmdump --listen-host 0.0.0.0 --listen-port 8080 --set block_global=false -s proxy_addons.py

# u should better unselect the checkbox Proxy Strict SSL here:
# https://docs.github.com/en/copilot/managing-copilot/configure-personal-settings/configuring-network-settings-for-github-copilot#configuring-a-proxy-in-visual-studio-code 


import asyncio
from mitmproxy import http, ctx
from datetime import datetime, timezone
import base64
import json
import os
import hashlib
import random
import traceback
import re

version_date = "20250908"

def generate_password(username: str, seed: int) -> str:
    random.seed(seed)
    random_prefix = str(random.randint(10000, 99999))
    input_string = f"{username}:{random_prefix}"
    hashed = hashlib.sha256(input_string.encode("utf-8")).hexdigest()
    return hashed[:10]

log_file_path = "auditlogs"

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
    "rin",
]


# Generate passwords for allowed users and save to user_auth.json
user_auth = {username: generate_password(username, random_seed) for username in allowed_usernames}

user_auth_file_path = os.path.join(log_file_path, "user_auth.json")
os.makedirs(os.path.dirname(user_auth_file_path), exist_ok=True)

try:
    with open(user_auth_file_path, "w", encoding='utf8') as user_auth_file:
        user_auth_file.write(json.dumps(user_auth, indent=4, ensure_ascii=False))
    ctx.log.info(f"✅ User authentication details saved to {user_auth_file_path}")
except Exception as e:
    ctx.log.error(f"❌ Unable to save user authentication details to file: {e}")


init_info = """
🔥🔥🔥🔥🔥🔥🔥🔥Init from here🔥🔥🔥🔥🔥🔥🔥🔥
version_date: %s
log_file_path: %s
conditional_judgment: %s
is_proxy_auth_needed: %s
random_seed: %s
allowed_usernames:\n- %s
""" % (version_date, log_file_path, conditional_judgment, is_proxy_auth_needed, random_seed, '\n- '.join(allowed_usernames))

ctx.log.info(init_info)


class RequestTypeKeywords:
    completions = r"v1/engines/(.*)/completions" # copilot-codex / gpt-4o-copilot
    chat = r"chat/completions"
    responses = r"/responses"          # Responses API (new endpoint for agent/Claude models)
    messages = r"/v1/messages"          # Messages API (Anthropic-style endpoint)
    extension = r"agents/(.*)"
    telemetry = r"/telemetry"

class RequestType:
    completions = "completions"
    chat = "chat"
    extension = "extension"
    telemetry = "telemetry"


def _has_nonempty_tools(content_request_dict):
    if not isinstance(content_request_dict, dict):
        return False

    tools = content_request_dict.get("tools")
    if isinstance(tools, list):
        return len(tools) > 0
    return bool(tools)


def _extension_name_from_header(x_onbehalf_extension_id):
    extension_id = x_onbehalf_extension_id.split("/", 1)[0]
    extension_parts = extension_id.split(".")
    return extension_parts[1] if len(extension_parts) > 1 else extension_parts[0]


def classify_action_type(
    request_type,
    content_request_dict,
    model,
    openai_intent,
    x_initiator,
    x_interaction_type,
    x_onbehalf_extension_id,
):
    model = model or "unknown"
    openai_intent = openai_intent or "unknown"
    content_request = str(content_request_dict.get('messages', [{}])[-2:]) if isinstance(content_request_dict, dict) else str(content_request_dict)
    action_type = "completions"

    if request_type == RequestType.chat:
        has_tools_in_body = _has_nonempty_tools(content_request_dict)
        # --- FIX: Check NES model FIRST, before agent classification ---
        # NES requests (copilot-nes-oct etc.) often carry x-initiator: agent
        # but are NOT agent conversations — they are code edit predictions.
        if "nes" in model:
            action_type = "nes"
        elif openai_intent == "conversation-agent" or x_initiator == "agent": # vscode / jetbrains (traditional)
            action_type = "agent"
        elif has_tools_in_body and openai_intent in ("conversation-panel", "conversation-other", "unknown"):
            # Newer Copilot versions (2025+) may not use "conversation-agent" header for agent mode,
            # but agent requests carry non-empty `tools` definitions for available tools.
            action_type = "agent"
        elif x_interaction_type == "git-commit": # jetbrains
            action_type = "commit-message"
        elif openai_intent == "conversation-edits" or x_interaction_type == "conversation-edit-panel": # vscode / jetbrains
            action_type = "edits"
        elif openai_intent == "conversation-panel":
            if "Write an explanation for the" in content_request: # vscode / jetbrains
                action_type = "explain"
            elif "Fix the provided errors and problems" in content_request: # jetbrains
                action_type = "fix"
            elif "Write documentation for the selected code" in content_request: # jetbrains
                action_type = "docs"
            elif "Write a set of unit tests for the code above" in content_request: # jetbrains
                action_type = "tests"
            else:
                action_type = "chat-panel"
        elif openai_intent == "conversation-inline":
            if "Please find a fix for my code so that the result is without any errors" in content_request: # vscode
                action_type = "fix"
            elif "Please, given sum, generate docstring only" in content_request: # vscode
                action_type = "docs"
            elif "Please, generate tests" in content_request or "Generate tests accordingly" in content_request: # vscode
                action_type = "tests"
            elif "I have the following code open in the editor" in content_request:
                action_type = "code-review"
            else:
                action_type = "chat-inline"
        elif openai_intent == "conversation-other":
            if x_onbehalf_extension_id is not None:
                action_type = _extension_name_from_header(x_onbehalf_extension_id)
            elif "<currentChange>" in content_request:
                action_type = "code-review"
            elif "<user-commits>" in content_request: # vscode
                action_type = "commit-message"
            else:
                action_type = "other"
        else:
            action_type = "other"
    elif request_type == RequestType.extension:
        action_type = "extension"

    return action_type

def get_request_type(flow: http.HTTPFlow):
    # ctx.log.warn(f"💗 flow.request.url: {flow.request.url}")
    # Determine type, discard if not one of the three types
    match = re.search(RequestTypeKeywords.completions, flow.request.url)
    if match:
        request_type = RequestType.completions
        para_in_url = match.group(1)
    else:
        match = re.search(RequestTypeKeywords.extension, flow.request.url)
        if match:
            request_type = RequestType.extension
            para_in_url = match.group(1).replace("?", "").replace("chat", "")
        elif RequestTypeKeywords.chat in flow.request.url:
            request_type = RequestType.chat
            para_in_url = None
        # --- NEW: Responses API & Messages API ---
        elif re.search(RequestTypeKeywords.responses, flow.request.url):
            request_type = RequestType.chat
            para_in_url = None
        elif re.search(RequestTypeKeywords.messages, flow.request.url):
            request_type = RequestType.chat
            para_in_url = None
        elif RequestTypeKeywords.telemetry in flow.request.url:
            request_type = RequestType.telemetry
            para_in_url = None
        else:
            request_type = None
            para_in_url = None
    # ctx.log.info(f"💗 request_type: {request_type}, para_in_url: {para_in_url}")
    return request_type, para_in_url


class ContentHandler:

    @staticmethod
    def is_convertible_to_json(string):
        try:
            json.loads(string)
            return True
        except (json.JSONDecodeError, TypeError, ValueError):
            return False

    @staticmethod
    def to_dicts(content):
        convert_status = True

        # for response content
        if content.startswith("data: "):
            contents = content.split("\n\n")
            ret = []
            for data in contents:
                data = data.split("data: ")[-1].strip()
                if data and data != "[DONE]":
                    try:
                        parsed = json.loads(data)
                        ret.append(parsed)
                    except (json.JSONDecodeError, ValueError):
                        ret.append(data)
        else:
            # for request content
            try:
                ret = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                ret = content
        if isinstance(ret, str):
            convert_status = False
            # ctx.log.error(f"❌ Content convert failed: {ret}")
        return ret, convert_status

    @staticmethod
    def pretty(content):
        print(json.dumps(ContentHandler.to_dicts(content=content), indent=4, ensure_ascii=False))


class ProxyReqRspSaveToFile:
    
    def __init__(self):
        self.usernames = {}
        self.usernames_file_path = os.path.join(log_file_path, "proxy_auth_cache.json")
        self.usage_file_path = os.path.join(log_file_path, "usage")
        self.metrics_file_path = os.path.join(log_file_path, "metrics")
        self.telemetry_file_path = os.path.join(log_file_path, "telemetry")
        self.current_date = datetime.now(timezone.utc).date()
        self.load_usernames()
        ctx.log.info("✅ Initialized ProxyReqRspSaveToJson plugin")

    def load_usernames(self):
        if os.path.exists(self.usernames_file_path):
            try:
                with open(self.usernames_file_path, "r", encoding='utf8') as usernames_file:
                    self.usernames = json.load(usernames_file)
                ctx.log.info(f"✅ Loaded usernames from {self.usernames_file_path}")
            except Exception as e:
                ctx.log.error(f"❌ Unable to load usernames from file: {e}")

    def save_usernames(self):
        try:
            with open(self.usernames_file_path, "w", encoding='utf8') as usernames_file:
                usernames_file.write(json.dumps(self.usernames, indent=4, ensure_ascii=False))
            ctx.log.info(f"✅ Usernames saved to {self.usernames_file_path}")
        except Exception as e:
            ctx.log.error(f"❌ Unable to save usernames to file: {e}")

    def requestheaders(self, flow: http.HTTPFlow):
        proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
        if proxy_auth:
            ctx.log.info(f"✅ Captured Proxy-Authorization in HTTP request header: {proxy_auth}")

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
        # The complete API request path cannot be obtained here
        # Headers in http_connect
        # {
        #     "host": "proxy.enterprise.githubcopilot.com:443",
        #     "Proxy-Connection": "keep-alive",
        #     "Proxy-Authorization": "Basic c2F0b21pYzo5NjFhYTg3NTNi",
        #     "Connection": "close"
        # }
        # {
        #     "Proxy-Authorization": "Basic c2F0b21pYzo5NjFhYTg3NTNi",
        #     "Host": "telemetry.enterprise.githubcopilot.com:443",
        #     "Proxy-Connection": "close"
        # }
            
        # in VSCode http://username:password@proxy_address:port
        # in JetBrains proxy_address port username password
        ctx.log.info(f"====================================================================================================")
        client_connect_address = flow.client_conn.address[0]
        ctx.log.info(f"✅ http_connect from {client_connect_address} to flow.request.url: {flow.request.url}")
    
        username, password = self.get_username_password(flow)
        if username != "anonymous":
            ctx.log.info(f"✅ Obtained Proxy-Authorization, username: {username}")
            self.usernames[client_connect_address] = username, password
            self.save_usernames()
        else:
            username, password = self.usernames.get(client_connect_address, ('anonymous', ''))
            if username == "anonymous":
                ctx.log.warn(f"⚠️ Anonymous user")
            else:
                ctx.log.info(f"💿 Using proxy auth cache: {username}, although Proxy-Authorization is missing")

    def response(self, flow: http.HTTPFlow):
        # The Proxy-Authorization cannot be obtained here

        # Headers in response completions
        # {
        #     "azureml-model-deployment": "d040-20241213214617",
        #     "content-security-policy": "default-src 'none'; sandbox",
        #     "content-type": "text/event-stream",
        #     "openai-processing-ms": "45.744",
        #     "strict-transport-security": "max-age=31536000",
        #     "x-request-id": "6c388e7e-66df-472a-9055-4ead8e168b97",
        #     "content-length": "356",
        #     "date": "Mon, 30 Dec 2024 01:18:57 GMT",
        #     "x-github-backend": "Kubernetes",
        #     "x-github-request-id": "80A8:391A24:10E20B:125859:6771F500"
        # }

        # Headers in response chat
        # {
        #     "content-security-policy": "default-src 'none'; sandbox",
        #     "content-type": "application/json",
        #     "strict-transport-security": "max-age=31536000",
        #     "x-request-id": "6b5df6f8-76f9-4964-8324-babeff8da62f",
        #     "date": "Mon, 30 Dec 2024 01:19:55 GMT",
        #     "x-github-backend": "Kubernetes",
        #     "x-github-request-id": "25B7:11694A:1967C6:2B8D5D:6771F539"
        # }

        client_connect_address = flow.client_conn.address[0]
        username, password = self.usernames.get(client_connect_address, ('anonymous', ''))

        # Determine type, discard if not one of the two types
        request_type, para_in_url = get_request_type(flow)

        # https://docs.github.com/en/copilot/managing-copilot/managing-github-copilot-in-your-organization/configuring-your-proxy-server-or-firewall-for-copilot
        # only proxy Telemetry and API Service for Completions, excluding GitHub.com for Authorization and User management
        if request_type:
            # ctx.log.info(f"✅ Processing http_connect: {flow.request.url}")
            if username != "anonymous":
                if is_proxy_auth_needed:
                    if username not in user_auth:
                        ctx.log.error(f"❌ Invalid username: {username}")
                        flow.response = http.Response.make(407)
                        return
                    if user_auth[username] != password:
                        ctx.log.error(f"❌ Invalid password {password} for user: {username}")
                        flow.response = http.Response.make(407)
                        return     
            else:
                if is_proxy_auth_needed:
                    ctx.log.error(f"❌ Missing Proxy-Authorization in request header, url: {flow.request.url}")
                    flow.response = http.Response.make(407)
                    return

        # Save request to local
        asyncio.ensure_future(self.save_to_file(flow))

    async def save_to_file(self, flow: http.HTTPFlow):
        # if "telemetry" not in flow.request.url:
        #     print("completions=================================: ", flow.request.url)

        # --- FIX: Skip non-POST requests (GET/OPTIONS/HEAD) ---
        # Extension polling (GET /agents/sessions?...) and OPTIONS preflight
        # requests contain no LLM content and create noise in usage-logs.
        if flow.request.method.upper() != "POST":
            ctx.log.info(f"⏭️ Skipping non-POST request: {flow.request.method} {flow.request.url[:120]}")
            return

        # Determine type, discard if not one of the two types
        request_type, para_in_url = get_request_type(flow)
        if not request_type:
            return

        request_type_emoji = "🤖🚗" if request_type == RequestType.completions else "💬👄"
        ctx.log.info(f"✅{request_type_emoji} Processing {request_type} response: {flow.request.url}")

        headers_request = dict(flow.request.headers)
        headers_response = dict(flow.response.headers)
        content_request = flow.request.content.decode('utf-8').replace('\"', '"') # .replace('"{', '{').replace('}"', '}').replace('\\', '').replace('"[', '[').replace(']"', ']').strip()
        content_request_dict, convert_status = ContentHandler.to_dicts(content_request)
        content_response = flow.response.content.decode('utf-8').replace('\"', '"')
        content_response_list, _ = ContentHandler.to_dicts(content_response)

        client_connect_address = flow.client_conn.address[0]
        username, password = self.usernames.get(client_connect_address, ('anonymous', ''))

        # Add milliseconds to the timestamp
        timeconsumed = round((flow.response.timestamp_end - flow.request.timestamp_start) * 1000, 2)
        timeconsumed_str = f"{timeconsumed}ms"  
        timestamp = datetime.now(timezone.utc).isoformat()

        action_type = "unknown"
        editor_version = "unknown"

        if request_type != RequestType.telemetry:
            editor_version = headers_request.get('editor-version', '-').replace('/', '-')
            x_initiator = headers_request.get('x-initiator', None)
            x_interaction_type = headers_request.get('x-interaction-type', None)
            model = content_request_dict.get('model', 'unknown') if request_type != RequestType.completions else para_in_url
            extension = para_in_url if request_type == RequestType.extension else None

            if conditional_judgment:
                # VSCode Conditional judgment
                if 'vscode' in editor_version.lower():
                    # Determine whether it is a normal completion
                    if request_type == RequestType.completions:
                        # If the completion response does not contain any text, it will be invalid.
                        has_text_in_contents_response = any([content.get('choices', [{}])[0].get('text') if isinstance(content, dict) else False for content in content_response_list])
                        if not has_text_in_contents_response:
                            ctx.log.warn(f'⚠️ Skipping invalid completion response, cuz there is no text in contents_response')
                            return
                    # For chat-type requests (chat, agent, edits, etc.), do NOT filter based on `stop` field.
                    # In newer Copilot versions (2025+), multi-turn conversations include `stop` in subsequent requests,
                    # which is normal behavior and should be recorded.

                # JetBrains Conditional judgment
                elif 'jetbrains' in editor_version.lower():
                    if request_type == RequestType.completions:
                        has_text_in_contents_response = any([content.get('choices', [{}])[0].get('text') if isinstance(content, dict) else False for content in content_response_list])
                        if not has_text_in_contents_response:
                            ctx.log.warn(f'⚠️ Skipping invalid completion response, cuz there is no text in contents_response')
                            return
                    # For chat-type requests in JetBrains, do NOT filter based on last_role or tools field.
                    # In agent mode, last message may be 'assistant' (tool call results) and tools field is always present.
                    # These are normal agent behaviors and should be recorded.

                else:
                    ctx.log.info(f"⚠️ Unknown editor: {editor_version}")

    
            # Concatenate string content
            language = content_request_dict.get('extra', {}).get('language', 'unknown')
            openai_intent = headers_request.get('openai-intent', 'unknown')
            x_onbehalf_extension_id = headers_request.get('x-onbehalf-extension-id', None)
            vscode_machineid = headers_request.get('vscode-machineid', '-')[0:10]
            

            # what type of action is this? chat or completions? or NES, Agent, Edit? 
            action_type = classify_action_type(
                request_type=request_type,
                content_request_dict=content_request_dict,
                model=model,
                openai_intent=openai_intent,
                x_initiator=x_initiator,
                x_interaction_type=x_interaction_type,
                x_onbehalf_extension_id=x_onbehalf_extension_id,
            )

            try:
                self.update_and_save_metrics(request_type, username, editor_version, language, action_type, model, extension)
            except Exception as e:
                ctx.log.error(f"❌ Unable to update metrics: {traceback.format_exc()}")

        else:
            if convert_status:
                
                vscode_machineid = "-"

                if isinstance(content_request_dict, list):
                    action_type = "telemetry"

                    for obj in content_request_dict:
                        
                        base_data = obj.get("data", {}).get("baseData", {})
                        properties = base_data.get("properties", {})

                        editor_version = "-".join(properties.get("editor_version", "unknown/unknown").split("/") if "/" in properties.get("editor_version", "unknown/unknown") else ["unknown", "unknown"])
                        language = properties.get("languageId", "unknown")
                        model = properties.get("engineName", "unknown")
                        
                        base_data_name = base_data.get("name")
                        num_lines = base_data.get("measurements", {}).get("numLines", 0)
                        if "hown" in base_data_name:
                            shown_num_lines = num_lines
                            accepted_num_lines = 0
                        elif "accepted" in base_data_name or "message" in base_data_name:
                            shown_num_lines = 0
                            accepted_num_lines = num_lines
                        else:
                            continue


                        try:
                            self.update_and_save_telemetry(username, editor_version, model, language, shown_num_lines, accepted_num_lines)
                        except Exception as e:
                            ctx.log.error(f"❌ Unable to update telemetry: {traceback.format_exc()}")


        if convert_status:

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
            directory_path = os.path.join(self.usage_file_path, username, action_type)
            os.makedirs(directory_path, exist_ok=True)

            log_file_name = f'{directory_path}/{timestamp}_{vscode_machineid}_{client_connect_address}_{editor_version}_{action_type}.json'.replace(':', '-')
            
            try:
                with open(log_file_name, "w", encoding='utf8') as log_file:
                    log_file.write(json.dumps(log_entry, indent=4, ensure_ascii=False))
                ctx.log.info(f"😄 Log saved {log_file_name}")
            except Exception as e:
                ctx.log.error(f"❌ Unable to save log to file: {traceback.format_exc()}")
                return

    def update_and_save_metrics(self, request_type, username, editor_version, language, action_type, model, extension):
        current_date = datetime.now(timezone.utc).date()
        if current_date != self.current_date:
            self.current_date = current_date
        self.metrics_file = os.path.join(self.metrics_file_path, f'copilot-usage_{self.current_date}.json')

        # Load existing metrics if the file exists
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r", encoding='utf8') as metrics_file:
                    existing_metrics = json.load(metrics_file)
                total_chat_turns = existing_metrics.get("total_chat_turns", 0)
                total_completions_count = existing_metrics.get("total_completions_count", 0)
                total_extension_count = existing_metrics.get("total_extension_count", 0)
                aggregated_metrics = existing_metrics.get("usage", {})
            except Exception as e:
                ctx.log.error(f"❌ Unable to load existing metrics: {traceback.format_exc()}")
                total_chat_turns = 0
                total_completions_count = 0
                total_extension_count = 0
                aggregated_metrics = {}
        else:
            total_chat_turns = 0
            total_completions_count = 0
            total_extension_count = 0
            aggregated_metrics = {}

        if username not in aggregated_metrics:
            aggregated_metrics[username] = {
                "chat_turns": 0,
                "chat": {},
                "completions_count": 0,
                "completions": {},
                "extension_count": 0,
                "extension": {}
            }

        if request_type == RequestType.completions:
            if editor_version not in aggregated_metrics[username]["completions"]:
                aggregated_metrics[username]["completions"][editor_version] = {
                    "count": 0,
                    "models": {}
                }
            
            # 更新编辑器版本的计数
            aggregated_metrics[username]["completions"][editor_version]["count"] += 1
            
            # 更新 models 统计作为 editor_version 的子集
            if model not in aggregated_metrics[username]["completions"][editor_version]["models"]:
                aggregated_metrics[username]["completions"][editor_version]["models"][model] = {
                    "count": 0,
                    "languages": {}
                }
            aggregated_metrics[username]["completions"][editor_version]["models"][model]["count"] += 1
            

            if language not in aggregated_metrics[username]["completions"][editor_version]["models"][model]["languages"]:
                aggregated_metrics[username]["completions"][editor_version]["models"][model]["languages"][language] = 0
            aggregated_metrics[username]["completions"][editor_version]["models"][model]["languages"][language] += 1
            
            aggregated_metrics[username]["completions_count"] += 1
            total_completions_count += 1
        elif request_type == RequestType.chat:
            if action_type not in aggregated_metrics[username]["chat"]:
                aggregated_metrics[username]["chat"][action_type] = {
                    "chat_turns": 0,
                    "editor_version": {}
                }
            
            # 更新 editor_version 统计，将 models 作为 editor_version 的子集
            if editor_version not in aggregated_metrics[username]["chat"][action_type]["editor_version"]:
                aggregated_metrics[username]["chat"][action_type]["editor_version"][editor_version] = {
                    "count": 0,
                    "models": {}
                }
            
            # 更新编辑器版本的计数
            aggregated_metrics[username]["chat"][action_type]["editor_version"][editor_version]["count"] += 1
            
            # 更新 models 统计作为 editor_version 的子集
            if model not in aggregated_metrics[username]["chat"][action_type]["editor_version"][editor_version]["models"]:
                aggregated_metrics[username]["chat"][action_type]["editor_version"][editor_version]["models"][model] = 0
            aggregated_metrics[username]["chat"][action_type]["editor_version"][editor_version]["models"][model] += 1
            
            aggregated_metrics[username]["chat"][action_type]["chat_turns"] += 1
            aggregated_metrics[username]["chat_turns"] += 1
            total_chat_turns += 1

        elif request_type == RequestType.extension:
            if extension not in aggregated_metrics[username]["extension"]:
                aggregated_metrics[username]["extension"][extension] = {
                    "count": 0,
                    "editor_version": {}
                }
            
            # 更新 editor_version 统计，将 models 作为 editor_version 的子集
            if editor_version not in aggregated_metrics[username]["extension"][extension]["editor_version"]:
                aggregated_metrics[username]["extension"][extension]["editor_version"][editor_version] = {
                    "count": 0,
                    "models": {}
                }
            
            # 更新编辑器版本的计数
            aggregated_metrics[username]["extension"][extension]["editor_version"][editor_version]["count"] += 1
            
            # 更新 models 统计作为 editor_version 的子集
            if model not in aggregated_metrics[username]["extension"][extension]["editor_version"][editor_version]["models"]:
                aggregated_metrics[username]["extension"][extension]["editor_version"][editor_version]["models"][model] = 0
            aggregated_metrics[username]["extension"][extension]["editor_version"][editor_version]["models"][model] += 1
            
            aggregated_metrics[username]["extension"][extension]["count"] += 1
            aggregated_metrics[username]["extension_count"] += 1
            total_extension_count += 1
        elif request_type == RequestType.telemetry:
            ctx.log.info(f"💤 Skipping telemetry data for metrics aggregation.")
        else:
            ctx.log.error(f"❌ Unknown request type: {request_type}")
            



        metrics_summary = {
            "day": str(self.current_date),
            "total_chat_turns": total_chat_turns,
            "total_completions_count": total_completions_count,
            "total_extension_count": total_extension_count,
            "usage": aggregated_metrics
        }

        # Create the metrics file if it does not exist.
        os.makedirs(self.metrics_file_path, exist_ok=True)

        try:
            with open(self.metrics_file, "w", encoding='utf8') as metrics_file:
                metrics_file.write(json.dumps(metrics_summary, indent=4, ensure_ascii=False))
            ctx.log.info(f"😆 Metrics saved {self.metrics_file}")
        except Exception as e:
            ctx.log.error(f"❌ Unable to save metrics to file: {e}")

    def update_and_save_telemetry(self, username, editor_version, model, language, shown_num_lines, accepted_num_lines):
        current_date = datetime.now(timezone.utc).date()
        if current_date != self.current_date:
            self.current_date = current_date

        # Define telemetry file path
        telemetry_file = os.path.join(self.telemetry_file_path, f'copilot-telemetry_{self.current_date}.json')

        # Load existing telemetry data if the file exists
        if os.path.exists(telemetry_file):
            try:
                with open(telemetry_file, "r", encoding='utf8') as file:
                    existing_telemetry = json.load(file)
                total_telemetry_events = existing_telemetry.get("total_telemetry_events", 0)
                global_shown_lines = existing_telemetry.get("total_shown_lines", 0)
                global_accepted_lines = existing_telemetry.get("total_accepted_lines", 0)
                line_statistics = existing_telemetry.get("line_statistics", {})
            except Exception as e:
                ctx.log.error(f"❌ Unable to load existing telemetry: {traceback.format_exc()}")
                total_telemetry_events = 0
                line_statistics = {}
        else:
            total_telemetry_events = 0
            global_shown_lines = 0
            global_accepted_lines = 0
            line_statistics = {}


        # Update telemetry counters
        total_telemetry_events += 1

        # Calculate global statistics
        global_shown_lines += shown_num_lines
        global_accepted_lines += accepted_num_lines
        global_acceptance_rate = round((global_accepted_lines / global_shown_lines) * 100, 2) if global_shown_lines > 0 else 0.0

        # Update line_statistics with nested structure: username -> editor_version -> model -> language
        if username not in line_statistics:
            line_statistics[username] = {}

        if editor_version not in line_statistics[username]:
            line_statistics[username][editor_version] = {}

        if model not in line_statistics[username][editor_version]:
            line_statistics[username][editor_version][model] = {}

        if language not in line_statistics[username][editor_version][model]:
            line_statistics[username][editor_version][model][language] = {
                "shown_lines": 0,
                "accepted_lines": 0
            }
        
        # Update the nested statistics
        line_statistics[username][editor_version][model][language]["shown_lines"] += shown_num_lines
        line_statistics[username][editor_version][model][language]["accepted_lines"] += accepted_num_lines

        # Prepare telemetry summary
        telemetry_summary = {
            "day": str(self.current_date),
            "total_telemetry_events": total_telemetry_events,
            "total_shown_lines": global_shown_lines,
            "total_accepted_lines": global_accepted_lines,
            "total_acceptance_rate": global_acceptance_rate,
            "total_users": len(line_statistics),
            "line_statistics": line_statistics
        }

        # Create the telemetry file directory if it does not exist
        os.makedirs(self.telemetry_file_path, exist_ok=True)

        # Save telemetry data
        try:
            with open(telemetry_file, "w", encoding='utf8') as file:
                file.write(json.dumps(telemetry_summary, indent=4, ensure_ascii=False))
            ctx.log.info(f"📊 Telemetry data saved {telemetry_file}")
        except Exception as e:
            ctx.log.error(f"❌ Unable to save telemetry data to file: {e}")

addons = [
    ProxyReqRspSaveToFile()
]
