from __future__ import annotations

from typing import Any, Dict

from core.base_handler import BaseHandler


class CustomSiteXHandler(BaseHandler):
    """示例：针对特定站点的自定义处理器。"""

    def can_handle(self, url: str) -> bool:
        return "site-x.example" in url

    def download(self, url: str, options: Dict[str, Any] | None = None) -> Any:
        return {
            "status": "pending",
            "handler": "custom-site-x",
            "url": url,
            "options": options or {},
        }
