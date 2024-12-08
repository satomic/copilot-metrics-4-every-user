# Copilot Proxy Insight

This project is a proxy tool to capture and log HTTP requests and responses, specifically designed to work with GitHub Copilot. Thanks Daniel Wang & [Lichao Zhao](https://github.com/lichaozhao/copilot-usage/blob/master/sample.py).


## WARNNING: BEFORE YOU TRY THIS TOOL, PLEASE READ THE FOLLOWING WARNNING CAREFULLY
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

- Captures HTTP requests and responses
- Logs request and response details to files
- Supports basic authentication


![architecture](files/architecture.png)


## How to Run

1. Prepare an intermediary server, [install mitmproxy](https://docs.mitmproxy.org/stable/overview-installation/). If you use pip to install mitmproxy on Windows, you need to add the exe path to the environment variable.
2. run command in console
```
mitmdump --listen-host 0.0.0.0 --listen-port 8080 --set block_global=false -s proxy_addons.py
```
3. now you can set the proxy in VSCode, and the IP address is `127.0.0.1`, please change it to the actual IP address.
4. However, at this time, VSCode will prompt for certificate errors, so a [certificate needs to be installed](https://docs.mitmproxy.org/stable/concepts-certificates/). The certificate download requires access to [mitm.it](mitm.it), and the prerequisite for normal access is that mitmproxy is functioning normally. Therefore, before enabling the proxy, only requests that go through the proxy will return normal web pages.
5. now you can use the Copilot to generate code, and the request and response will be saved in the `logs` folder. the `completions` folder will save the completions of the Copilot. the `telemetry` folder will save the telemetry of the Copilot.

## log samples


![log_samples](files/log_samples.png)



### `completions` log 

`2024-12-08T13-05-57.639893_4ce93ec3b2_127.0.0.1_satomic_vscode-1.95.3.json`

```json
{
    "proxy-authorization": "satomic",
    "timestamp": "2024-12-08T13:18:23.331449",
    "proxy-time-consumed": "382.4ms",
    "request": {
        "url": "https://proxy.enterprise.githubcopilot.com/v1/engines/copilot-codex/completions",
        "method": "POST",
        "headers": {
            "authorization": "Bearer tid=5e1e32dca6b1cccb036ab1bd2d7d444d;ol=679c1c3c27523244c3c3ad04ef88d2f0;exp=1733664598;sku=copilot_enterprise_seat;proxy-ep=proxy.enterprise.githubcopilot.com;st=dotcom;ssc=1;chat=1;cit=1;malfil=1;ccr=1;8kp=1;ip=183.212.229.191;asn=AS56046:fd1cc3e11a1f994287c361f4e01464ea88ced12ac102d593f99e0662724b9c97",
            "x-request-id": "d4392923-fe05-4c6a-babc-37f66954bee6",
            "openai-organization": "github-copilot",
            "vscode-sessionid": "ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208",
            "vscode-machineid": "4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9",
            "editor-version": "vscode/1.95.3",
            "editor-plugin-version": "copilot/1.248.0",
            "copilot-language-server-version": "1.248.0",
            "annotations-enabled": "true",
            "code-quote-enabled": "true",
            "openai-intent": "copilot-ghost",
            "content-type": "application/json",
            "user-agent": "GithubCopilot/1.248.0",
            "content-length": "548",
            "accept": "*/*",
            "accept-encoding": "gzip,deflate,br"
        },
        "content": "{\"prompt\":\"[]: # Path: readme.md\\n# Copilot Proxy Insight\\n\\nThis project is a proxy tool to capture and log HTTP requests and responses, specifically designed to work with GitHub Copilot.\\n\\n## Features\\n\\n- Captures HTTP requests and responses\\n- Logs request and response details to files\\n- Supports basic authentication\\n\\n## How to Run\",\"suffix\":\"\",\"max_tokens\":500,\"temperature\":0,\"top_p\":1,\"n\":1,\"stop\":[\"\\n\\n\\n\"],\"stream\":true,\"extra\":{\"language\":\"markdown\",\"next_indent\":0,\"trim_by_indentation\":true,\"prompt_tokens\":67,\"suffix_tokens\":0}}"
    },
    "response": {
        "status_code": 200,
        "headers": {
            "azureml-model-deployment": "d169-20240925214105",
            "content-security-policy": "default-src 'none'; sandbox",
            "content-type": "text/event-stream",
            "openai-processing-ms": "41.1556",
            "strict-transport-security": "max-age=31536000",
            "x-request-id": "d4392923-fe05-4c6a-babc-37f66954bee6",
            "content-length": "367",
            "date": "Sun, 08 Dec 2024 13:18:23 GMT",
            "x-github-backend": "Kubernetes",
            "x-github-request-id": "793D:3AE21:3087E1:352BF1:67559C9E"
        },
        "content": "data: {\"id\":\"cmpl-AcBSxNRroE6mLsEEz9UOfcJPcyGMK\",\"created\":1733663903,\"model\":\"gpt-35-turbo\",\"choices\":[{\"index\":0,\"finish_reason\":null,\"logprobs\":null,\"p\":\"aaaaaaa\"}]}\n\ndata: {\"id\":\"cmpl-AcBSxNRroE6mLsEEz9UOfcJPcyGMK\",\"created\":1733663903,\"model\":\"gpt-35-turbo\",\"choices\":[{\"text\":\"\\n\",\"index\":0,\"finish_reason\":\"stop\",\"logprobs\":null,\"p\":\"aaaaaa\"}]}\n\ndata: [DONE]\n\n"
    }
}
```

### `telemetry` log 


`2024-12-08T13-05-59.677800_-_127.0.0.1_satomic_-.json`


```json
{
    "proxy-authorization": "satomic",
    "timestamp": "2024-12-08T13:28:23.121297",
    "proxy-time-consumed": "530.51ms",
    "request": {
        "url": "https://telemetry.enterprise.githubcopilot.com/telemetry",
        "method": "POST",
        "headers": {
            "content-type": "application/json",
            "user-agent": "GithubCopilot/1.248.0",
            "content-length": "9732",
            "accept": "*/*",
            "accept-encoding": "gzip,deflate,br"
        },
        "content": "[{\"time\":\"2024-12-08T13:28:07.023Z\",\"iKey\":\"7d7048df-6dd0-4048-bb23-b716c1461f8f\",\"name\":\"Microsoft.ApplicationInsights.7d7048df6dd04048bb23b716c1461f8f.Event\",\"tags\":{\"ai.session.id\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"ai.user.id\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"ai.cloud.roleInstance\":\"REDACTED\",\"ai.device.osVersion\":\"Windows_NT 10.0.26100\",\"ai.device.osArchitecture\":\"x64\",\"ai.device.osPlatform\":\"win32\",\"ai.cloud.role\":\"Web\",\"ai.application.ver\":\"1.248.0\",\"ai.internal.sdkVersion\":\"javascript:3.3.4\"},\"data\":{\"baseType\":\"EventData\",\"baseData\":{\"ver\":2,\"name\":\"copilot/request.sent\",\"properties\":{\"endpoint\":\"completions\",\"engineName\":\"copilot-codex\",\"uiKind\":\"ghostText\",\"request_option_max_tokens\":\"500\",\"request_option_temperature\":\"0\",\"request_option_top_p\":\"1\",\"request_option_n\":\"1\",\"request_option_stop\":\"[\\\"\\\\n\\\\n\\\\n\\\"]\",\"request_option_stream\":\"true\",\"request_option_extra\":\"{\\\"language\\\":\\\"markdown\\\",\\\"next_indent\\\":0,\\\"trim_by_indentation\\\":true,\\\"prompt_tokens\\\":359,\\\"suffix_tokens\\\":0}\",\"headerRequestId\":\"25fa5824-5df2-4d24-80d5-9c3288365dd3\",\"github_copilot_inlineSuggest_enable\":\"true\",\"copilot_build\":\"1246\",\"copilot_buildType\":\"prod\",\"copilot_trackingId\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"organizations_list\":\"679c1c3c27523244c3c3ad04ef88d2f0\",\"enterprise_list\":\"208076\",\"sku\":\"copilot_enterprise_seat\",\"editor_version\":\"vscode/1.95.3\",\"editor_plugin_version\":\"copilot/1.248.0\",\"client_machineid\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"client_sessionid\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"copilot_version\":\"copilot/1.248.0\",\"runtime_version\":\"node/20.18.0\",\"common_extname\":\"copilot\",\"common_extversion\":\"1.248.0\",\"common_vscodeversion\":\"vscode/1.95.3\",\"fetcher\":\"HelixFetcher\",\"proxy_enabled\":\"true\",\"proxy_auth\":\"true\",\"proxy_kerberos_spn\":\"false\",\"reject_unauthorized\":\"true\",\"VSCode.ABExp.Features\":\"aa_t_chat;account-aacf;copilotcppheaders;livesharecontinuousaa;mindaroBinariesVersion;portForwardingServiceEnabled-development;portForwardingServiceEnabled-production;portForwardingServiceEnabled-staging;shouldUseGrpcService\",\"abexp.assignmentcontext\":\"vsliv368:30146709;vspor879:30202332;vspor708:30202333;vspor363:30204092;binariesv615:30325510;vsaa593cf:30376535;c4g48928:30535728;aa_t_chat:31080850;vsc_trt_9033:31086482;\",\"unique_id\":\"d0526136-a6b2-4196-873e-31f1e8fdf595\",\"common_os\":\"win32\",\"common_platformversion\":\"10.0.26100\",\"common_vscodemachineid\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"common_vscodesessionid\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"common_uikind\":\"desktop\",\"common_remotename\":\"none\",\"common_isnewappinstall\":\"\"},\"measurements\":{\"promptCharLen\":1487,\"timeSinceIssuedMs\":1,\"current_time\":1733664487}}}},{\"time\":\"2024-12-08T13:28:08.912Z\",\"iKey\":\"7d7048df-6dd0-4048-bb23-b716c1461f8f\",\"name\":\"Microsoft.ApplicationInsights.7d7048df6dd04048bb23b716c1461f8f.Event\",\"tags\":{\"ai.session.id\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"ai.user.id\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"ai.cloud.roleInstance\":\"REDACTED\",\"ai.device.osVersion\":\"Windows_NT 10.0.26100\",\"ai.device.osArchitecture\":\"x64\",\"ai.device.osPlatform\":\"win32\",\"ai.cloud.role\":\"Web\",\"ai.application.ver\":\"1.248.0\",\"ai.internal.sdkVersion\":\"javascript:3.3.4\"},\"data\":{\"baseType\":\"EventData\",\"baseData\":{\"ver\":2,\"name\":\"copilot/networking.cancelRequest\",\"properties\":{\"headerRequestId\":\"25fa5824-5df2-4d24-80d5-9c3288365dd3\",\"github_copilot_inlineSuggest_enable\":\"true\",\"copilot_build\":\"1246\",\"copilot_buildType\":\"prod\",\"copilot_trackingId\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"organizations_list\":\"679c1c3c27523244c3c3ad04ef88d2f0\",\"enterprise_list\":\"208076\",\"sku\":\"copilot_enterprise_seat\",\"editor_version\":\"vscode/1.95.3\",\"editor_plugin_version\":\"copilot/1.248.0\",\"client_machineid\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"client_sessionid\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"copilot_version\":\"copilot/1.248.0\",\"runtime_version\":\"node/20.18.0\",\"common_extname\":\"copilot\",\"common_extversion\":\"1.248.0\",\"common_vscodeversion\":\"vscode/1.95.3\",\"fetcher\":\"HelixFetcher\",\"proxy_enabled\":\"true\",\"proxy_auth\":\"true\",\"proxy_kerberos_spn\":\"false\",\"reject_unauthorized\":\"true\",\"VSCode.ABExp.Features\":\"aa_t_chat;account-aacf;copilotcppheaders;livesharecontinuousaa;mindaroBinariesVersion;portForwardingServiceEnabled-development;portForwardingServiceEnabled-production;portForwardingServiceEnabled-staging;shouldUseGrpcService\",\"abexp.assignmentcontext\":\"vsliv368:30146709;vspor879:30202332;vspor708:30202333;vspor363:30204092;binariesv615:30325510;vsaa593cf:30376535;c4g48928:30535728;aa_t_chat:31080850;vsc_trt_9033:31086482;\",\"unique_id\":\"025077aa-c960-4011-8424-8377d6e24476\",\"common_os\":\"win32\",\"common_platformversion\":\"10.0.26100\",\"common_vscodemachineid\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"common_vscodesessionid\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"common_uikind\":\"desktop\",\"common_remotename\":\"none\",\"common_isnewappinstall\":\"\"},\"measurements\":{\"timeSinceIssuedMs\":2,\"current_time\":1733664488}}}},{\"time\":\"2024-12-08T13:28:08.914Z\",\"iKey\":\"7d7048df-6dd0-4048-bb23-b716c1461f8f\",\"name\":\"Microsoft.ApplicationInsights.7d7048df6dd04048bb23b716c1461f8f.Event\",\"tags\":{\"ai.session.id\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"ai.user.id\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"ai.cloud.roleInstance\":\"REDACTED\",\"ai.device.osVersion\":\"Windows_NT 10.0.26100\",\"ai.device.osArchitecture\":\"x64\",\"ai.device.osPlatform\":\"win32\",\"ai.cloud.role\":\"Web\",\"ai.application.ver\":\"1.248.0\",\"ai.internal.sdkVersion\":\"javascript:3.3.4\"},\"data\":{\"baseType\":\"EventData\",\"baseData\":{\"ver\":2,\"name\":\"copilot/ghostText.canceled\",\"properties\":{\"headerRequestId\":\"25fa5824-5df2-4d24-80d5-9c3288365dd3\",\"github_copilot_inlineSuggest_enable\":\"true\",\"copilot_build\":\"1246\",\"copilot_buildType\":\"prod\",\"copilot_trackingId\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"organizations_list\":\"679c1c3c27523244c3c3ad04ef88d2f0\",\"enterprise_list\":\"208076\",\"sku\":\"copilot_enterprise_seat\",\"languageId\":\"markdown\",\"beforeCursorWhitespace\":\"false\",\"afterCursorWhitespace\":\"true\",\"promptChoices\":\"{\\\"used\\\":{\\\"BeforeCursor\\\":351,\\\"PathMarker\\\":8},\\\"unused\\\":{\\\"LanguageMarker\\\":7},\\\"usedCounts\\\":{\\\"BeforeCursor\\\":22,\\\"PathMarker\\\":1},\\\"unusedCounts\\\":{\\\"LanguageMarker\\\":1}}\",\"promptBackground\":\"{\\\"used\\\":[],\\\"unused\\\":[]}\",\"neighborSource\":\"[[\\\"opentabs\\\",[]]]\",\"gitRepoInformation\":\"unavailable\",\"engineName\":\"copilot-codex\",\"isMultiline\":\"true\",\"blockMode\":\"server\",\"isCycling\":\"false\",\"editor_version\":\"vscode/1.95.3\",\"editor_plugin_version\":\"copilot/1.248.0\",\"client_machineid\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"client_sessionid\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"copilot_version\":\"copilot/1.248.0\",\"runtime_version\":\"node/20.18.0\",\"common_extname\":\"copilot\",\"common_extversion\":\"1.248.0\",\"common_vscodeversion\":\"vscode/1.95.3\",\"fetcher\":\"HelixFetcher\",\"proxy_enabled\":\"true\",\"proxy_auth\":\"true\",\"proxy_kerberos_spn\":\"false\",\"reject_unauthorized\":\"true\",\"VSCode.ABExp.Features\":\"aa_t_chat;account-aacf;copilotcppheaders;livesharecontinuousaa;mindaroBinariesVersion;portForwardingServiceEnabled-development;portForwardingServiceEnabled-production;portForwardingServiceEnabled-staging;shouldUseGrpcService\",\"abexp.assignmentcontext\":\"vsliv368:30146709;vspor879:30202332;vspor708:30202333;vspor363:30204092;binariesv615:30325510;vsaa593cf:30376535;c4g48928:30535728;aa_t_chat:31080850;vsc_trt_9033:31086482;\",\"fileType\":\"markdown\",\"timeBucket\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"unique_id\":\"3f9d62d3-2c9f-4644-bde7-94335a2fc3fe\",\"endpoint\":\"completions\",\"uiKind\":\"ghostText\",\"temperature\":\"0\",\"n\":\"1\",\"stop\":\"unset\",\"logit_bias\":\"null\",\"reason\":\"network request aborted\",\"cancelledNetworkRequest\":\"true\",\"common_os\":\"win32\",\"common_platformversion\":\"10.0.26100\",\"common_vscodemachineid\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"common_vscodesessionid\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"common_uikind\":\"desktop\",\"common_remotename\":\"none\",\"common_isnewappinstall\":\"\"},\"measurements\":{\"promptCharLen\":1487,\"promptEndPos\":1486,\"documentLength\":1500,\"delayMs\":0,\"promptComputeTimeMs\":6,\"contextualFilterScore\":0.6060606231031178,\"timeSinceIssuedMs\":1975,\"current_time\":1733664486}}}},{\"time\":\"2024-12-08T13:28:15.190Z\",\"iKey\":\"7d7048df-6dd0-4048-bb23-b716c1461f8f\",\"name\":\"Microsoft.ApplicationInsights.7d7048df6dd04048bb23b716c1461f8f.Event\",\"tags\":{\"ai.session.id\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"ai.user.id\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"ai.cloud.roleInstance\":\"REDACTED\",\"ai.device.osVersion\":\"Windows_NT 10.0.26100\",\"ai.device.osArchitecture\":\"x64\",\"ai.device.osPlatform\":\"win32\",\"ai.cloud.role\":\"Web\",\"ai.application.ver\":\"1.248.0\",\"ai.internal.sdkVersion\":\"javascript:3.3.4\"},\"data\":{\"baseType\":\"EventData\",\"baseData\":{\"ver\":2,\"name\":\"copilot/prompt.stat\",\"properties\":{\"headerRequestId\":\"2371b6f1-56a6-4910-89d9-cf28edd34d58\",\"copilot_trackingId\":\"5e1e32dca6b1cccb036ab1bd2d7d444d\",\"sku\":\"copilot_enterprise_seat\",\"organizations_list\":\"679c1c3c27523244c3c3ad04ef88d2f0\",\"enterprise_list\":\"208076\",\"unique_id\":\"b1f1a3c9-7572-4b25-abea-db755c0b9f5f\",\"common_extname\":\"copilot\",\"common_extversion\":\"1.248.0\",\"common_vscodeversion\":\"vscode/1.95.3\",\"common_os\":\"win32\",\"common_platformversion\":\"10.0.26100\",\"common_vscodemachineid\":\"4ce93ec3b250003c9580aba5d1a71685fe7df281ac090fa58018e5b6a3017bf9\",\"common_vscodesessionid\":\"ea6d81ed-3ef8-4d7f-9094-0225bd5022071733632427208\",\"common_uikind\":\"desktop\",\"common_remotename\":\"none\",\"common_isnewappinstall\":\"\"},\"measurements\":{}}}}]"
    },
    "response": {
        "status_code": 200,
        "headers": {
            "content-security-policy": "default-src 'none'; sandbox",
            "content-type": "application/json; charset=utf-8",
            "date": "Sun, 08 Dec 2024 13:28:23 GMT",
            "strict-transport-security": "max-age=31536000, max-age=31536000",
            "x-content-type-options": "nosniff, nosniff",
            "x-frame-options": "DENY",
            "x-xss-protection": "0",
            "content-length": "62",
            "x-github-backend": "Kubernetes",
            "x-github-request-id": "7D34:2048F4:103A49D:193BC43:67559EE8",
            "server": "github.com"
        },
        "content": "{\"itemsReceived\":3,\"itemsAccepted\":3,\"appId\":null,\"errors\":[]}"
    }
}
```


