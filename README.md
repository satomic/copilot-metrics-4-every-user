# Copilot Proxy Insight
This project is a proxy tool to capture and log HTTP requests and responses, specifically designed to work with GitHub Copilot.

## Update Note
2024-12-08
- Add the feature of recording completions and telemetry of Copilot.

2024-12-25
- By default, telemetry logs are not saved, you can enable it by remove the annotation symbol from line 16 in `proxy_addons.py`.
- Added parsing of the content fields of request and response in completion

2024-12-26
- Feature: Read proxy authentication information (proxy_auth_info). If it contains ":", use the left part as the username directory, otherwise it is the username directly; and save the log to the corresponding subdirectory according to the URL containing "copilot-codex/completions" or "chat/completions", otherwise skip the record.
- Feature: The log file name no longer contains proxy_auth_info.

2024-12-28
- Feature: Enhance proxy_addons.py to track usage metrics and save to separate files; refactor logging paths and update metrics handling

2024-12-29
- Feature: Add filtering for meaningless requests to ensure that only valuable data is calculated


## Warning
- these are general guidelines for copilot block:
    1. **Do not change any GitHub Copilot http headers on network**
    2. Do not share GitHub accounts and GitHub Copilot access
        - GitHub personal account can not be shared, GitHub can block those shared accounts.
        - GitHub Copilot access can not be shared between multiple users.
    3. Maintain a single GitHub Copilot access network outbound so one user do not access GitHub Copilot from different locations at the same time
    4. do not use a program to generate copilot token, the token need to be requested from official GitHub Copilot IDE extension
- GitHub does not recommend customer on solution that is not part of GitHub product, in the case of internet proxy officially GitHub support will not support issues on proxy or advise which proxy to use.


---

## Features

### Normal Features
- **Proxy traffic**. For a network-isolated development environment.
- **Prompts Recording**. Captures HTTP requests and responses and logs the details to files, **this will let you know exactly what the code snippets (prompts) uploaded by Copilot are**.

![architecture_no_header_add](files/architecture_no_header_add.png)



### Advanced Features
- **User Insight**. Supports basic authentication, this allows you to get the data of the user dimension, more deeper than team dimension. (this will change http header, not recommanded)

![architecture](files/architecture.png)


## How to Run

1. Prepare an intermediary server, [install mitmproxy](https://docs.mitmproxy.org/stable/overview-installation/). If you use pip to install mitmproxy on Windows, you need to add the exe path to the environment variable.
2. run command in console
    ```bash
    mitmdump --listen-host 0.0.0.0 --listen-port 8080 --set block_global=false -s proxy_addons.py
    ```
3. now you can set the proxy in your IDE (VSCode as example here), and the IP address is `127.0.0.1`, please change it to your actual IP address.
    - for normal features, set the proxy like this: `http://127.0.0.1:8080`
        ![proxy](files/proxy.png)
    - for advanced features, set the proxy like this: `http://your_username@127.0.0.1:8080`, and add the `Proxy-Authorization` header with the value `your_username` (the username is `satomic` in the sample code).
        ![proxy_add_header](files/proxy_add_header.png)
        or in `settings.json`
        ```json
            "http.proxy": "http:satomic:<YOUR_BASIC_PWD>//127.0.0.1:8080"
        ```
4. However, at this time, IDE will prompt certificate errors, so a [certificate needs to be installed](https://docs.mitmproxy.org/stable/concepts-certificates/). The certificate download requires access to [mitm.it](mitm.it), and the prerequisite for normal access is that mitmproxy is functioning normally. Therefore, before enabling the proxy, only requests that go through the proxy will return normal web pages.
5. now you can use the Copilot to generate code, and the request and response will be saved in the `logs` folder. 
    - The `metrics` folder stores daily usage statistics. 
    - The `usage` folder is a subdirectory with the user name, which records the detailed data of `chat` and `completions` respectively.


## log samples


![log_samples](files/log_samples.png)


### usage log
```json
{
    "day": "2024-12-28",
    "total_chat_turns": 13,
    "total_completions_count": 19,
    "usage": {
        "satomic": {
            "chat_turns": 6,
            "completions_count": 16,
            "chat": {
                "vscode-1.96.2": 6
            },
            "completions": {
                "vscode-1.96.2": {
                    "python": 2,
                    "javascript": 3,
                    "markdown": 11
                }
            }
        },
        "xuefeng": {
            "chat_turns": 7,
            "completions_count": 3,
            "chat": {
                "JetBrains-PC-243.22562.220": 6,
                "vscode-1.96.2": 1
            },
            "completions": {
                "JetBrains-PC-243.22562.220": {
                    "python": 3
                }
            }
        }
    }
}
```


### `completions` log 

```json
{
    "proxy-authorization": "satomic:123",
    "timestamp": "2024-12-28T14:50:18.214725",
    "proxy-time-consumed": "188.35ms",
    "request": {
        "url": "https://proxy.enterprise.githubcopilot.com/v1/engines/copilot-codex/completions",
        "method": "POST",
        "headers": {
            "authorization": "Bearer tid=5e1e32dca6b1cccb036ab1bd2d7d444d;ol=ea9395b9a9248c05ee6847cbd24355ed,fa25d2808d3f1461923caba5bbaa7673,679c1c3c27523244c3c3ad04ef88d2f0;exp=1735398336;sku=copilot_enterprise_seat;proxy-ep=proxy.enterprise.githubcopilot.com;st=dotcom;ssc=1;chat=1;cit=1;malfil=1;ccr=1;8kp=1;ip=156.59.13.4;asn=AS21859:f9c792ae49b6494b595fc62854ed0a10a78e624d849112f33114fefde749863b",
            "x-request-id": "2e177ccd-029e-46f1-bf59-3d366bdb5e55",
            "openai-organization": "github-copilot",
            "vscode-sessionid": "d680c0d9-d9ef-43b5-a272-86ad27f0b04e1735381508063",
            "vscode-machineid": "4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9",
            "x-github-api-version": "2024-12-15",
            "editor-version": "vscode/1.96.2",
            "editor-plugin-version": "copilot/1.254.0",
            "copilot-language-server-version": "1.254.0",
            "annotations-enabled": "true",
            "code-quote-enabled": "true",
            "openai-intent": "copilot-ghost",
            "content-type": "application/json",
            "user-agent": "GithubCopilot/1.254.0",
            "content-length": "306",
            "accept": "*/*",
            "accept-encoding": "gzip,deflate,br"
        },
        "content": {
            "prompt": "# Path: tryit.py\n\n\n\ndef add(x, y):\n    return x + y",
            "suffix": "",
            "max_tokens": 500,
            "temperature": 0,
            "top_p": 1,
            "n": 1,
            "stop": [
                "\n"
            ],
            "nwo": "satomic/copilot-proxy-insight",
            "stream": true,
            "extra": {
                "language": "python",
                "next_indent": 0,
                "trim_by_indentation": true,
                "prompt_tokens": 18,
                "suffix_tokens": 0
            }
        }
    },
    "response": {
        "status_code": 200,
        "headers": {
            "azureml-model-deployment": "d071-20241226110228",
            "content-security-policy": "default-src 'none'; sandbox",
            "content-type": "text/event-stream",
            "openai-processing-ms": "33.6402",
            "strict-transport-security": "max-age=31536000",
            "x-request-id": "2e177ccd-029e-46f1-bf59-3d366bdb5e55",
            "content-length": "356",
            "date": "Sat, 28 Dec 2024 14:50:18 GMT",
            "x-github-backend": "Kubernetes",
            "x-github-request-id": "8566:18E3C2:19397A5:1A0ECB8:67700FE2"
        },
        "content": [
            {
                "id": "cmpl-AjSQstOuqLSedY7J3Vg6Op6Khvcnl",
                "created": 1735397418,
                "model": "gpt-35-turbo",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": null,
                        "logprobs": null,
                        "p": "aaaaaaa"
                    }
                ]
            },
            {
                "id": "cmpl-AjSQstOuqLSedY7J3Vg6Op6Khvcnl",
                "created": 1735397418,
                "model": "gpt-35-turbo",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "logprobs": null,
                        "p": "aaaaaaa"
                    }
                ]
            },
            ""
        ]
    }
}
```
