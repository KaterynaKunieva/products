import asyncio
from enum import Enum
from http.client import InvalidURL
from typing import Dict, Any
import functools as ft
from aiohttp import ClientSession, ClientResponse, ClientResponseError, ClientConnectionError, ClientPayloadError, \
    ServerTimeoutError
import logging

from scripts.base_entities import ProductInfo


class HttpMethod(str, Enum):
    Get = "get",
    Post = "post",
    Delete = "delete",
    Head = "head",
    Patch = "patch"


class HttpResponseType(str, Enum):
    Text = "text",
    Json = "json"

async def call_method(url: str, params: Dict[str, str] = None,
                      headers: Dict[str, str] = None, payload: Dict[str, str] = None, method: HttpMethod = HttpMethod.Get, response_body_type: HttpResponseType = HttpResponseType.Json) -> Dict[str, Any]:
    async with ClientSession() as session:
        if method == HttpMethod.Get:
            request_manager = session.get(url, params=params, headers=headers, json=payload)
        elif method == HttpMethod.Post:
            request_manager = session.post(url, params=params, headers=headers, json=payload)
        else:
            raise Exception("Http method not implemented")
        response = None
        status = None
        http_response = None
        try:
            http_response: ClientResponse = await request_manager
            status = http_response.status
            response = await http_response.text() if response_body_type == response_body_type.Text else await http_response.json()

        except ClientResponseError as error:
            logging.error(
                f"Server response error, status: {error.status}, message: {error.message}, url: {error.request_info.url}, headers: {str(error.request_info.headers)}",
                exc_info=error)
        except ServerTimeoutError as error:
            logging.error(f"Server timeout error", exc_info=error)
        except ClientPayloadError as payload_error:
            logging.error(
                f"Client payload error", exc_info=payload_error)
        except ClientConnectionError as connection_error:
            logging.error(f"Client connection error, ", exc_info=connection_error)
        except InvalidURL as url_exception:
            logging.error(f"InvalidURL error", exc_info=url_exception)
        except Exception as error:
            logging.error("Unknown exception happened", exc_info=error)
        
        return {
            "response": response,
            "status": status,
            "http_response": http_response
        }

async def get_http_response(url: str, params: Dict[str, str] = None,
                      headers: Dict[str, str] = None, payload: Dict[str, str] = None, method: HttpMethod = HttpMethod.Get, response_body_type: HttpResponseType = HttpResponseType.Json) -> Any:
    logging.debug(f"Http requesting {url}...")
    return (await call_method(url, params, headers, payload, method, response_body_type)).get("response")

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def async_cmd(func):  # to do, write your function decorator
    @ft.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper
