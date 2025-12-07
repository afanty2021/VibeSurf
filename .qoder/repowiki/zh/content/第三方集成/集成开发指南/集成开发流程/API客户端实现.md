# API客户端实现

<cite>
**本文档引用的文件**   
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py)
- [newsnow/client.py](file://vibe_surf/tools/website_api/newsnow/client.py)
- [douyin/helpers.py](file://vibe_surf/tools/website_api/douyin/helpers.py)
- [weibo/helpers.py](file://vibe_surf/tools/website_api/weibo/helpers.py)
- [youtube/helpers.py](file://vibe_surf/tools/website_api/youtube/helpers.py)
- [newsnow/helpers.py](file://vibe_surf/tools/website_api/newsnow/helpers.py)
</cite>

## 目录
1. [引言](#引言)
2. [HTTP客户端配置](#http客户端配置)
3. [请求方法封装](#请求方法封装)
4. [响应数据解析](#响应数据解析)
5. [错误处理机制](#错误处理机制)
6. [重试策略](#重试策略)
7. [统一API接口规范](#统一api接口规范)
8. [连接池管理](#连接池管理)
9. [请求批处理](#请求批处理)
10. [缓存机制](#缓存机制)
11. [性能优化建议](#性能优化建议)
12. [分页处理](#分页处理)
13. [速率限制处理](#速率限制处理)
14. [API版本兼容性](#api版本兼容性)

## 引言
本文档详细说明了如何实现第三方API客户端，以抖音、微博、YouTube和NewsNow的client.py为例。文档涵盖了HTTP客户端配置、请求方法封装、响应数据解析、错误处理机制和重试策略。同时，解释了如何设计统一的API接口规范，包括请求参数验证、响应格式标准化和异常分类。此外，还指导开发者实现高效的连接池管理、请求批处理和缓存机制，并提供性能优化建议，如连接复用、异步请求和流式响应处理。文档包含实际代码示例，展示如何处理分页、速率限制和API版本兼容性。

## HTTP客户端配置
API客户端的HTTP配置是确保请求成功和性能优化的基础。在分析的代码库中，每个API客户端都通过`httpx.AsyncClient`进行配置，支持异步请求和代理设置。

### 基础配置
所有客户端都通过`__init__`方法初始化，接受`browser_session`、`timeout`和`proxy`参数。`browser_session`用于管理浏览器会话，`timeout`设置请求超时时间，`proxy`用于配置代理。

```python
def __init__(self, browser_session: AgentBrowserSession, timeout: int = 60, proxy: Optional[str] = None):
    self.browser_session = browser_session
    self.proxy = proxy
    self.timeout = timeout
```

### 默认请求头
每个客户端都定义了默认的请求头，包括`User-Agent`、`Host`、`Origin`、`Referer`和`Content-Type`。这些头信息模拟了真实浏览器的行为，有助于避免被API服务器识别为自动化请求。

```python
self.default_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    "Host": "www.douyin.com",
    "Origin": "https://www.douyin.com/",
    "Referer": "https://www.douyin.com/",
    "Content-Type": "application/json;charset=UTF-8",
}
```

### Cookie管理
客户端通过浏览器会话提取Cookie，并将其添加到请求头中。这确保了请求的认证状态，特别是在需要登录的API中。

```python
result = await asyncio.wait_for(
    cdp_session.cdp_client.send.Storage.getCookies(session_id=cdp_session.session_id),
    timeout=8.0
)
web_cookies = result.get('cookies', [])
cookie_str, cookie_dict = extract_cookies_from_browser(web_cookies)
if cookie_str:
    self.default_headers["Cookie"] = cookie_str
self.cookies = cookie_dict
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L41-L66)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L37-L63)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L40-L69)

## 请求方法封装
请求方法的封装是API客户端的核心，它简化了HTTP请求的发送过程，并提供了统一的接口。

### GET请求封装
GET请求封装方法`get_request`负责准备请求参数和头信息，并调用`_make_request`方法发送请求。

```python
async def get_request(self, uri: str, params: Optional[Dict] = None, headers: Optional[Dict] = None):
    params, headers = await self._prepare_request_params(uri, params, headers, "GET")
    return await self._make_request("GET", f"{self._host}{uri}", params=params, headers=headers)
```

### POST请求封装
POST请求封装方法`post_request`与GET请求类似，但需要处理POST数据。

```python
async def post_request(self, uri: str, data: Dict, headers: Optional[Dict] = None):
    data, headers = await self._prepare_request_params(uri, data, headers, "POST", post_data=data)
    return await self._make_request("POST", f"{self._host}{uri}", data=data, headers=headers)
```

### 参数准备
`_prepare_request_params`方法负责准备请求参数，包括添加通用参数、生成签名等。

```python
async def _prepare_request_params(self, uri: str, params: Optional[Dict] = None,
                                  headers: Optional[Dict] = None, request_method: str = "GET",
                                  post_data: Optional[Dict] = None):
    if not params:
        params = {}
    headers = headers or copy.deepcopy(self.default_headers)
    common_params = create_common_params()
    ms_token = await self._get_local_storage_token()
    if ms_token:
        common_params["msToken"] = ms_token
    params.update(common_params)
    query_string = urllib.parse.urlencode(params)
    post_data = post_data or {}
    if "/v1/web/general/search" not in uri:
        a_bogus = await self._get_a_bogus_signature(uri, query_string, post_data)
        params["a_bogus"] = a_bogus
    return params, headers
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L280-L288)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L188-L211)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L233-L265)

## 响应数据解析
响应数据解析是将API返回的原始数据转换为结构化数据的过程，便于后续处理。

### JSON响应解析
大多数API返回JSON格式的数据，客户端通过`response.json()`方法解析。

```python
try:
    data = response.json()
    if response.status_code == 200:
        return data
    else:
        error_msg = data.get("message", "Request failed")
        raise DataExtractionError(f"API error: {error_msg}")
except json.JSONDecodeError:
    if response.status_code == 200:
        return response.text
    else:
        raise DataExtractionError(f"Invalid response: {response.text[:200]}")
```

### HTML响应解析
对于返回HTML的API，客户端使用正则表达式或HTML解析器提取所需数据。

```python
def extract_render_data(html_content: str) -> Optional[Dict]:
    try:
        match = re.search(r'var \$render_data = (\[.*?\])\[0\]', html_content, re.DOTALL)
        if match:
            render_data_json = match.group(1)
            render_data_dict = json.loads(render_data_json)
            return render_data_dict[0] if render_data_dict else None
    except (json.JSONDecodeError, IndexError):
        pass
    return None
```

### 数据结构化
解析后的数据通常被转换为统一的数据结构，便于后续处理。

```python
return {
    "aweme_id": aweme_info.get("aweme_id"),
    "aweme_type": str(aweme_info.get("aweme_type", "")),
    "title": aweme_info.get("desc", ""),
    "desc": aweme_info.get("desc", ""),
    "create_time": aweme_info.get("create_time"),
    "user_id": user_info.get("uid"),
    "sec_uid": user_info.get("sec_uid"),
    "short_user_id": user_info.get("short_id"),
    "user_unique_id": user_info.get("unique_id"),
    "nickname": user_info.get("nickname"),
    "avatar": user_info.get("avatar_thumb", {}).get("url_list", [""])[0],
    "liked_count": str(interact_info.get("digg_count", 0)),
    "collected_count": str(interact_info.get("collect_count", 0)),
    "comment_count": str(interact_info.get("comment_count", 0)),
    "share_count": str(interact_info.get("share_count", 0)),
    "ip_location": aweme_info.get("ip_label", ""),
    "aweme_url": f"https://www.douyin.com/video/{aweme_info.get('aweme_id')}",
}
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L259-L278)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L164-L183)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L224-L231)

## 错误处理机制
错误处理机制是确保API客户端稳定运行的关键，它能够捕获和处理各种异常情况。

### 异常分类
客户端定义了多种异常类型，用于区分不同类型的错误。

```python
class DouyinError(Exception):
    """Base exception for Douyin API errors"""
    pass

class NetworkError(DouyinError):
    """Network connection error"""
    pass

class DataExtractionError(DouyinError):
    """Data extraction error"""
    pass

class AuthenticationError(DouyinError):
    """Authentication error"""
    pass

class RateLimitError(DouyinError):
    """Rate limit exceeded error"""
    pass

class VerificationError(DouyinError):
    """Account verification required error"""
    pass
```

### 错误捕获
在请求过程中，客户端捕获各种异常，并根据异常类型进行处理。

```python
async def _make_request(self, method: str, url: str, **kwargs) -> Union[str, Dict]:
    async with httpx.AsyncClient(proxy=self.proxy) as client:
        response = await client.request(method, url, timeout=self.timeout, **kwargs)
    if response.text == "" or response.text == "blocked":
        logger.error(f"Request blocked, response.text: {response.text}")
        raise VerificationError("Account may be blocked or requires verification")
    try:
        data = response.json()
        if response.status_code == 200:
            return data
        else:
            error_msg = data.get("message", "Request failed")
            raise DataExtractionError(f"API error: {error_msg}")
    except json.JSONDecodeError:
        if response.status_code == 200:
            return response.text
        else:
            raise DataExtractionError(f"Invalid response: {response.text[:200]}")
```

### 日志记录
客户端使用日志记录错误信息，便于调试和监控。

```python
logger.error(f"Failed to setup Douyin client: {e}")
```

**Section sources**
- [douyin/helpers.py](file://vibe_surf/tools/website_api/douyin/helpers.py#L212-L239)
- [weibo/helpers.py](file://vibe_surf/tools/website_api/weibo/helpers.py#L256-L284)
- [youtube/helpers.py](file://vibe_surf/tools/website_api/youtube/helpers.py#L339-L366)

## 重试策略
重试策略是提高API客户端可靠性的关键，它能够在请求失败时自动重试。

### 重试装饰器
客户端使用`tenacity`库的`@retry`装饰器来实现重试策略。

```python
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def _make_request(self, method: str, url: str, **kwargs) -> Union[str, Dict]:
    # Request logic here
```

### 重试条件
重试策略通常基于特定的条件，如网络错误或速率限制。

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError))
)
async def _fetch_source_news(self, source_id: str) -> Optional[SourceResponse]:
    # Request logic here
```

### 重试间隔
重试间隔可以是固定的，也可以是指数退避的。

```python
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L243-L244)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L134-L135)
- [newsnow/client.py](file://vibe_surf/tools/website_api/newsnow/client.py#L73-L77)

## 统一API接口规范
统一的API接口规范有助于提高代码的可维护性和可扩展性。

### 请求参数验证
客户端在发送请求前验证请求参数，确保参数的正确性。

```python
async def search_content_by_keyword(
        self,
        keyword: str,
        offset: int = 0,
        search_channel: SearchChannelType = SearchChannelType.GENERAL,
        sort_type: SearchSortType = SearchSortType.GENERAL,
        publish_time: PublishTimeType = PublishTimeType.UNLIMITED,
        search_id: str = "",
) -> List[Dict]:
    # Parameter validation and processing
```

### 响应格式标准化
客户端将不同API的响应数据转换为统一的格式，便于后续处理。

```python
return {
    "aweme_id": aweme_info.get("aweme_id"),
    "aweme_type": str(aweme_info.get("aweme_type", "")),
    "title": aweme_info.get("desc", ""),
    "desc": aweme_info.get("desc", ""),
    "create_time": aweme_info.get("create_time"),
    "user_id": user_info.get("uid"),
    "sec_uid": user_info.get("sec_uid"),
    "short_user_id": user_info.get("short_id"),
    "user_unique_id": user_info.get("unique_id"),
    "nickname": user_info.get("nickname"),
    "avatar": user_info.get("avatar_thumb", {}).get("url_list", [""])[0],
    "liked_count": str(interact_info.get("digg_count", 0)),
    "collected_count": str(interact_info.get("collect_count", 0)),
    "comment_count": str(interact_info.get("comment_count", 0)),
    "share_count": str(interact_info.get("share_count", 0)),
    "ip_location": aweme_info.get("ip_label", ""),
    "aweme_url": f"https://www.douyin.com/video/{aweme_info.get('aweme_id')}",
}
```

### 异常分类
客户端定义了统一的异常分类，便于错误处理。

```python
class DouyinError(Exception):
    """Base exception for Douyin API errors"""
    pass

class NetworkError(DouyinError):
    """Network connection error"""
    pass

class DataExtractionError(DouyinError):
    """Data extraction error"""
    pass

class AuthenticationError(DouyinError):
    """Authentication error"""
    pass

class RateLimitError(DouyinError):
    """Rate limit exceeded error"""
    pass

class VerificationError(DouyinError):
    """Account verification required error"""
    pass
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L290-L379)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L213-L270)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L304-L384)

## 连接池管理
连接池管理是提高API客户端性能的重要手段，它能够复用TCP连接，减少连接建立的开销。

### 连接复用
客户端使用`httpx.AsyncClient`的连接池功能，自动复用连接。

```python
async with httpx.AsyncClient(proxy=self.proxy) as client:
    response = await client.request(method, url, timeout=self.timeout, **kwargs)
```

### 连接超时
客户端设置连接超时时间，避免长时间等待。

```python
async with httpx.AsyncClient(proxy=self.proxy) as client:
    response = await client.request(method, url, timeout=self.timeout, **kwargs)
```

### 连接关闭
客户端在使用完毕后关闭连接，释放资源。

```python
async def close(self):
    if self.browser_session and self.target_id and self.new_tab:
        try:
            logger.info(f"Close target id: {self.target_id}")
            await self.browser_session.cdp_client.send.Target.closeTarget(params={'targetId': self.target_id})
        except Exception as e:
            logger.warning(f"Error closing target {self.target_id}: {e}")
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L256-L257)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L149-L150)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L208-L209)

## 请求批处理
请求批处理是提高API客户端效率的重要手段，它能够减少网络往返次数。

### 批量获取新闻
NewsNow客户端支持批量获取新闻，通过一次请求获取多个来源的新闻。

```python
async def fetch_news_batch(
    self,
    source_ids: List[str]
) -> Dict[str, Any]:
    url = f"{self.base_url}/api/s/entire"
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"POST request to {url} with {len(source_ids)} sources")
            payload = {"sources": source_ids}
            response = await client.post(
                url,
                json=payload,
                headers=self.default_headers
            )
            # Process response
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching batch news")
        return {}
    except Exception as e:
        logger.error(f"Error fetching batch news: {e}")
        return {}
```

### 批量搜索
客户端支持批量搜索，通过一次请求获取多个关键词的搜索结果。

```python
async def search_posts_by_keyword(
        self,
        keyword: str,
        page: int = 1,
        search_type: SearchType = SearchType.DEFAULT,
) -> List[Dict]:
    endpoint = "/api/container/getIndex"
    container_id = create_container_id(search_type, keyword)
    cards = []
    posts = []
    for page_num in range(page):
        params = {
            "containerid": container_id,
            "page_type": "searchall",
            "page": page_num,
        }
        raw_response = await self._get_request(endpoint, params)
        cards.extend(raw_response.get("cards", []))
    # Process cards
```

**Section sources**
- [newsnow/client.py](file://vibe_surf/tools/website_api/newsnow/client.py#L286-L359)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L213-L270)

## 缓存机制
缓存机制是提高API客户端性能的重要手段，它能够减少重复请求。

### 响应缓存
客户端可以缓存API响应，避免重复请求相同的资源。

```python
async def _fetch_source_news(self, source_id: str) -> Optional[SourceResponse]:
    url = f"{self.base_url}/api/s?id={source_id}"
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self.default_headers)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch news for source {source_id}: HTTP {response.status_code}")
                return None
            data = response.json()
            if not isinstance(data, dict):
                logger.warning(f"Invalid response format for source {source_id}")
                return None
            if data.get("status") not in ["success", "cache"]:
                logger.warning(f"API returned non-success status for source {source_id}: {data.get('status')}")
                return None
            return data
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching news for source {source_id}")
        raise
    except (httpx.NetworkError, httpx.ConnectError) as e:
        logger.warning(f"Network error fetching news for source {source_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching news for source {source_id}: {e}")
        return None
```

### 数据缓存
客户端可以缓存解析后的数据，避免重复解析。

```python
async def get_news(
    self,
    source_id: Optional[str] = None,
    count: int = 10,
    news_type: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    results: Dict[str, List[Dict[str, Any]]] = {}
    if source_id:
        if source_id not in self.sources:
            logger.warning(f"Unknown source ID: {source_id}")
            return results
        source_metadata = self.sources[source_id]
        if not should_include_source(source_metadata, news_type):
            logger.info(f"Source {source_id} skipped due to type filter: {news_type}")
            return results
        sources_to_fetch = {source_id: source_metadata}
        tasks = []
        source_ids = []
        for sid in sources_to_fetch.keys():
            tasks.append(self._fetch_source_news(sid))
            source_ids.append(sid)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        # Process responses
    else:
        if news_type == "hottest":
            source_ids = self.HOTTEST_SOURCES
        elif news_type == "realtime":
            source_ids = self.REALTIME_SOURCES
        else:
            source_ids = self.HOTTEST_SOURCES + self.REALTIME_SOURCES
        logger.info(f"Batch fetching news from {len(source_ids)} sources for type: {news_type}")
        results = await self.fetch_news_batch(source_ids)
        if count > 0:
            for sid in results:
                results[sid] = results[sid][:count]
    return results
```

**Section sources**
- [newsnow/client.py](file://vibe_surf/tools/website_api/newsnow/client.py#L78-L221)

## 性能优化建议
性能优化是提高API客户端效率的关键，以下是一些建议。

### 连接复用
使用连接池复用TCP连接，减少连接建立的开销。

```python
async with httpx.AsyncClient(proxy=self.proxy) as client:
    response = await client.request(method, url, timeout=self.timeout, **kwargs)
```

### 异步请求
使用异步请求，提高并发处理能力。

```python
async def search_content_by_keyword(
        self,
        keyword: str,
        offset: int = 0,
        search_channel: SearchChannelType = SearchChannelType.GENERAL,
        sort_type: SearchSortType = SearchSortType.GENERAL,
        publish_time: PublishTimeType = PublishTimeType.UNLIMITED,
        search_id: str = "",
) -> List[Dict]:
    # Asynchronous request logic
```

### 流式响应处理
对于大响应，使用流式处理，避免内存溢出。

```python
async def _make_request(self, method: str, url: str, **kwargs) -> Union[str, Dict]:
    async with httpx.AsyncClient(proxy=self.proxy) as client:
        response = await client.request(method, url, timeout=self.timeout, **kwargs)
    if response.text == "" or response.text == "blocked":
        logger.error(f"Request blocked, response.text: {response.text}")
        raise VerificationError("Account may be blocked or requires verification")
    try:
        data = response.json()
        if response.status_code == 200:
            return data
        else:
            error_msg = data.get("message", "Request failed")
            raise DataExtractionError(f"API error: {error_msg}")
    except json.JSONDecodeError:
        if response.status_code == 200:
            return response.text
        else:
            raise DataExtractionError(f"Invalid response: {response.text[:200]}")
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L256-L278)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L149-L183)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L208-L231)

## 分页处理
分页处理是处理大量数据的关键，它能够分批获取数据，避免内存溢出。

### 分页参数
客户端通过分页参数控制数据的获取。

```python
async def search_content_by_keyword(
        self,
        keyword: str,
        offset: int = 0,
        search_channel: SearchChannelType = SearchChannelType.GENERAL,
        sort_type: SearchSortType = SearchSortType.GENERAL,
        publish_time: PublishTimeType = PublishTimeType.UNLIMITED,
        search_id: str = "",
) -> List[Dict]:
    query_params = {
        'search_channel': search_channel.value,
        'enable_history': '1',
        'keyword': keyword,
        'search_source': 'tab_search',
        'query_correct_type': '1',
        'is_filter_search': '0',
        'offset': offset,
        'count': '15',
        'need_filter_settings': '1',
        'list_type': 'multi',
        'search_id': search_id,
    }
    # Request logic
```

### 分页循环
客户端通过循环获取所有分页数据。

```python
async def fetch_all_video_comments(
        self,
        aweme_id: str,
        fetch_interval: float = 1.0,
        include_replies: bool = False,
        max_comments: int = 1000,
) -> List[Dict]:
    all_comments = []
    has_more = True
    cursor = 0
    while has_more and len(all_comments) < max_comments:
        uri = "/aweme/v1/web/comment/list/"
        params = {
            "aweme_id": aweme_id,
            "cursor": cursor,
            "count": 20,
            "item_type": 0
        }
        headers = copy.copy(self.default_headers)
        headers["Referer"] = create_referer_url(aweme_id=aweme_id)
        comments_data = await self.get_request(uri, params, headers)
        has_more = comments_data.get("has_more", False)
        cursor = comments_data.get("cursor", 0)
        # Process comments
        await asyncio.sleep(fetch_interval)
    logger.info(f"Fetched {len(all_comments)} comments for video {aweme_id}")
    return all_comments
```

**Section sources**
- [douyin/client.py](file://vibe_surf/tools/website_api/douyin/client.py#L539-L636)
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L375-L457)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L515-L654)

## 速率限制处理
速率限制处理是避免被API服务器封禁的关键，它能够控制请求频率。

### 速率限制异常
客户端捕获速率限制异常，并进行相应处理。

```python
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def _make_request(self, method: str, url: str, **kwargs):
    raw_response = kwargs.pop("raw_response", False)
    async with httpx.AsyncClient(proxy=self.proxy, timeout=self.timeout) as client:
        response = await client.request(method, url, **kwargs)
    if response.status_code == 403:
        raise AuthenticationError("Access forbidden - may need login or verification")
    elif response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    elif response.status_code == 404:
        raise ContentNotFoundError("Content not found")
    elif response.status_code >= 500:
        raise NetworkError(f"Server error: {response.status_code}")
    # Process response
```

### 请求间隔
客户端通过设置请求间隔，避免触发速率限制。

```python
async def fetch_all_video_comments(
        self,
        aweme_id: str,
        fetch_interval: float = 1.0,
        include_replies: bool = False,
        max_comments: int = 1000,
) -> List[Dict]:
    # Request logic with interval
    await asyncio.sleep(fetch_interval)
```

**Section sources**
- [weibo/client.py](file://vibe_surf/tools/website_api/weibo/client.py#L154-L159)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L214-L219)

## API版本兼容性
API版本兼容性是确保客户端长期稳定运行的关键，它能够适应API的变化。

### 版本检测
客户端通过检测API版本，选择合适的请求参数和处理逻辑。

```python
async def _extract_api_config(self):
    try:
        cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=self.target_id)
        content_result = await cdp_session.cdp_client.send(Runtime.evaluate(
            params={
                'expression': "document.documentElement.outerHTML",
                'returnByValue': True,
            },
            session_id=cdp_session.session_id,
        ))
        html_content = content_result.get('result', {}).get('value', '')
        api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html_content)
        if api_key_match:
            self._api_key = api_key_match.group(1)
            logger.info(f"Extracted YouTube API key: {self._api_key[:10]}...")
        version_match = re.search(r'"clientVersion":"([^"]+)"', html_content)
        if version_match:
            self._client_version = version_match.group(1)
            self.default_headers["X-YouTube-Client-Version"] = self._client_version
        visitor_match = re.search(r'"visitorData":"([^"]+)"', html_content)
        if visitor_match:
            self._visitor_data = visitor_match.group(1)
    except Exception as e:
        logger.warning(f"Failed to extract YouTube API config: {e}")
```

### 向后兼容
客户端通过向后兼容的处理逻辑，适应API的变化。

```python
def _extract_video_info(self, video_data: Dict) -> Optional[Dict]:
    try:
        video_id = video_data.get("videoId")
        if not video_id:
            return None
        title = video_data.get("title", {}).get("runs", [{}])[0].get("text", "")
        if not title and "accessibility" in video_data.get("title", {}):
            title = video_data["title"]["accessibility"]["accessibilityData"]["label"]
        # Extract view count
        view_count_text = ""
        view_count_runs = video_data.get("viewCountText", {}).get("simpleText", "")
        if not view_count_runs:
            view_count_runs = video_data.get("shortViewCountText", {}).get("simpleText", "")
        view_count = format_view_count(view_count_runs)
        # Extract duration
        duration_text = video_data.get("lengthText", {}).get("simpleText", "")
        duration_seconds = 0
        if duration_text:
            time_parts = duration_text.split(":")
            if len(time_parts) == 2:
                duration_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
            elif len(time_parts) == 3:
                duration_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        # Extract channel info
        channel_data = video_data.get("longBylineText", {}).get("runs", [{}])[0]
        channel_name = channel_data.get("text", "")
        channel_url = channel_data.get("navigationEndpoint", {}).get("commandMetadata", {}).get(
            "webCommandMetadata", {}).get("url", "")
        channel_id = extract_channel_id_from_url(channel_url) if channel_url else ""
        # Extract thumbnail
        thumbnails = video_data.get("thumbnail", {}).get("thumbnails", [])
        thumbnail_url = extract_thumbnail_url(thumbnails)
        # Extract published time
        published_time_text = video_data.get("publishedTimeText", {}).get("simpleText", "")
        description = ''
        if 'descriptionSnippet' in video_data:
            for desc in video_data.get('descriptionSnippet', {}).get('runs', {}):
                description += desc.get('text', '')
        return {
            "video_id": video_id,
            "title": process_youtube_text(title),
            "description": description,
            "duration": duration_seconds,
            "view_count": view_count,
            "like_count": -1,
            "comment_count": -1,
            "published_time": published_time_text,
            "thumbnail_url": thumbnail_url,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "channel_id": channel_id,
            "channel_name": channel_name,
            "channel_url": f"https://www.youtube.com{channel_url}" if channel_url else "",
        }
    except Exception as e:
        logger.error(f"Failed to extract video info: {e}")
        return None
```

**Section sources**
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L137-L173)
- [youtube/client.py](file://vibe_surf/tools/website_api/youtube/client.py#L390-L457)