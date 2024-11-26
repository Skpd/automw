import base64
import os
from urllib.parse import parse_qsl

from dotenv import load_dotenv
from requests import request

from mosbot.common.logger import get_logger


def handler(event, context):
    # load env from parent directory
    load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../.env"))

    logger = get_logger('proxy', verbose=True)

    proxy_host = os.getenv("PROXY_HOST", None)
    if proxy_host is None:
        raise Exception(f"PROXY_HOST env var is required but set to {proxy_host=}.")

    try:
        url = f"{proxy_host}{event['rawPath']}"
        if event['rawQueryString']:
            url += "?{event['rawQueryString']}"
        logger.debug(f"Proxy {url=}")

        cookies = {}
        for cookie in event.get('cookies', []):
            k, v = cookie.split('=', 1)
            cookies[k] = v
        logger.debug(f"Proxy {cookies=}")
        method = event['requestContext']['http']['method']
        headers = event.get('headers', {})
        body = event.get('body', None)
        if body:
            body = dict(parse_qsl(base64.b64decode(body).decode('ascii')))
        if 'user-agent' in headers:
            headers['user-agent'] = "don't throttle plz " + headers['user-agent']
    except Exception as e:
        logger.error(f"Failed to build request: {type(e).__name__} {e}")
        status_code = 503
        headers = {}
        content = f"Failed to build request: {type(e).__name__} {e}"
        cookies = {}
        return {
            "statusCode": status_code,
            "headers": headers,
            "body": content,
            "cookies": cookies
        }

    try:
        logger.debug(f"Requesting {method.upper()} {url} with {cookies=}, {headers=}, and {body=}")
        response = request(method, url, cookies=cookies, headers=headers, data=body, allow_redirects=False)
        status_code = response.status_code
        logger.debug(f"Response {status_code=}")
        headers = response.headers
        headers.pop('content-encoding', None)
        headers = dict(headers)
        logger.debug(f"Response {headers=}")
        content = base64.b64encode(response.content).decode('ascii')
        logger.debug(f"Response {content=}")
        cookies = ['='.join(x) for x in response.cookies.items()]
        logger.debug(f"Response {cookies=}")
    except Exception as e:
        logger.error(f"Request failed: {type(e).__name__} {e}")
        status_code = 503
        headers = {}
        content = f"Request failed: {type(e).__name__} {e}"
        cookies = {}

    return {
        "statusCode": status_code,
        "headers": headers,
        "body": content,
        "cookies": cookies,
        "isBase64Encoded": True
    }
