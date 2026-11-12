"""YApi MCP Server - 读取 YApi 接口文档的 MCP 服务"""

import json
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

YAPI_HOST = os.environ.get("YAPI_HOST", "http://yapi.dev.visaapp6.com")
YAPI_TOKEN = os.environ.get("YAPI_TOKEN", "")
YAPI_PROJECT_ID = os.environ.get("YAPI_PROJECT_ID", "16")

mcp = FastMCP("yapi")


def _base_url() -> str:
    return YAPI_HOST.rstrip("/")


def _token() -> str:
    if not YAPI_TOKEN:
        raise ValueError("YAPI_TOKEN 环境变量未配置")
    return YAPI_TOKEN


async def _yapi_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = {"token": _token(), **(params or {})}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{_base_url()}{path}", params=query)
        response.raise_for_status()
        data = response.json()
    if data.get("errcode") != 0:
        raise RuntimeError(f"YApi 请求失败: {data.get('errmsg', '未知错误')}")
    return data.get("data", {})


def _parse_yapi_url(url: str) -> dict[str, int | None]:
    """从 YApi URL 解析 project_id 和 interface_id"""
    project_match = re.search(r"/project/(\d+)", url)
    interface_match = re.search(r"/interface/api/(\d+)", url)
    return {
        "project_id": int(project_match.group(1)) if project_match else None,
        "interface_id": int(interface_match.group(1)) if interface_match else None,
    }


def _normalize_interface(data: dict[str, Any]) -> dict[str, Any]:
    """将 YApi 接口数据归一化为易读格式"""
    req_body = data.get("req_body_other") or data.get("req_body_form")
    if isinstance(req_body, str) and req_body.strip():
        try:
            req_body = json.loads(req_body)
        except json.JSONDecodeError:
            pass

    res_body = data.get("res_body")
    if isinstance(res_body, str) and res_body.strip():
        try:
            res_body = json.loads(res_body)
        except json.JSONDecodeError:
            pass

    return {
        "id": data.get("_id"),
        "title": data.get("title"),
        "method": data.get("method"),
        "path": data.get("path"),
        "status": data.get("status"),
        "catid": data.get("catid"),
        "desc": data.get("desc") or data.get("markdown"),
        "headers": data.get("req_headers", []),
        "query": data.get("req_query", []),
        "pathParams": data.get("req_params", []),
        "bodyType": data.get("req_body_type"),
        "bodySchema": req_body,
        "responseSchema": res_body,
    }


def _flatten_menu(menu: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将分类菜单展平为接口列表"""
    interfaces = []
    for category in menu:
        cat_name = category.get("name", "")
        for item in category.get("list", []):
            interfaces.append(
                {
                    "id": item.get("_id"),
                    "title": item.get("title"),
                    "method": item.get("method"),
                    "path": item.get("path"),
                    "category": cat_name,
                    "status": item.get("status"),
                }
            )
    return interfaces


@mcp.tool()
async def get_interface(
    interface_id: int | None = None,
    url: str | None = None,
    include_raw: bool = False,
) -> str:
    """获取单个 YApi 接口详情。

    Args:
        interface_id: 接口 ID
        url: YApi 接口页面 URL，如 http://yapi.example.com/project/16/interface/api/123
        include_raw: 是否包含原始 YApi 数据
    """
    if url:
        parsed = _parse_yapi_url(url)
        interface_id = parsed.get("interface_id")

    if not interface_id:
        raise ValueError("请提供 interface_id 或包含接口 ID 的 url")

    data = await _yapi_get("/api/interface/get", {"id": interface_id})
    result: dict[str, Any] = {"interface": _normalize_interface(data)}
    if include_raw:
        result["raw"] = data
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_project_interfaces(
    project_id: int | None = None,
    url: str | None = None,
) -> str:
    """获取 YApi 项目的接口目录（按分类分组）。

    Args:
        project_id: 项目 ID，默认使用环境变量 YAPI_PROJECT_ID
        url: YApi 项目页面 URL，如 http://yapi.example.com/project/16/interface/api
    """
    if url:
        parsed = _parse_yapi_url(url)
        project_id = parsed.get("project_id")

    if not project_id:
        project_id = int(YAPI_PROJECT_ID)

    menu = await _yapi_get("/api/interface/list_menu", {"project_id": project_id})
    categories = []
    total = 0
    for category in menu:
        items = category.get("list", [])
        total += len(items)
        categories.append(
            {
                "id": category.get("_id"),
                "name": category.get("name"),
                "desc": category.get("desc"),
                "count": len(items),
                "interfaces": [
                    {
                        "id": item.get("_id"),
                        "title": item.get("title"),
                        "method": item.get("method"),
                        "path": item.get("path"),
                        "status": item.get("status"),
                    }
                    for item in items
                ],
            }
        )

    return json.dumps(
        {"project_id": project_id, "total": total, "categories": categories},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def search_project_interfaces(
    keyword: str,
    project_id: int | None = None,
    page: int = 1,
    limit: int = 20,
) -> str:
    """按关键字搜索 YApi 项目接口。

    Args:
        keyword: 搜索关键字（匹配接口标题或路径）
        project_id: 项目 ID，默认使用环境变量 YAPI_PROJECT_ID
        page: 页码，从 1 开始
        limit: 每页数量
    """
    if not project_id:
        project_id = int(YAPI_PROJECT_ID)

    data = await _yapi_get(
        "/api/interface/list",
        {"project_id": project_id, "page": page, "limit": limit, "keyword": keyword},
    )

    interfaces = [
        {
            "id": item.get("_id"),
            "title": item.get("title"),
            "method": item.get("method"),
            "path": item.get("path"),
            "status": item.get("status"),
        }
        for item in data.get("list", [])
    ]

    return json.dumps(
        {
            "project_id": project_id,
            "keyword": keyword,
            "page": page,
            "limit": limit,
            "total": data.get("count", len(interfaces)),
            "interfaces": interfaces,
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def get_project_info(project_id: int | None = None) -> str:
    """获取 YApi 项目基本信息。

    Args:
        project_id: 项目 ID，默认使用环境变量 YAPI_PROJECT_ID
    """
    if not project_id:
        project_id = int(YAPI_PROJECT_ID)

    data = await _yapi_get("/api/project/get", {"id": project_id})
    return json.dumps(
        {
            "id": data.get("_id"),
            "name": data.get("name"),
            "desc": data.get("desc"),
            "basepath": data.get("basepath"),
            "env": data.get("env", []),
        },
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
