from .ytdlp_handler import YTDLPHandler
from handlers.generic_hls_handler import GenericHLSHandler
class DownloadManager:
    def __init__(self):
        self.handlers = []
        # 注册兜底的 yt-dlp
        self.register_handler(YTDLPHandler())
        # 注册刚写的强制 HLS 解析器（后注册的在前面，优先级更高）
        self.register_handler(GenericHLSHandler())

    def get_handler_for_url(self, url: str):
        """根据 URL 查找对应的处理器实例"""
        for handler in self.handlers:
            if handler.can_handle(url):
                return handler
        return None

    def register_handler(self, handler):
        self.handlers.insert(0, handler)

    def get_info(self, url: str) -> dict | None:
        """新增：分发解析任务"""
        for handler in self.handlers:
            if handler.can_handle(url):
                return handler.get_info(url)
        return None

    def start_download(self, url: str, save_path: str, format_id: str, log_callback=None):
        """修改：透传 format_id"""
        for handler in self.handlers:
            if handler.can_handle(url):
                return handler.download(url, save_path, format_id, log_callback)
        if log_callback: log_callback("❌ 无匹配的处理器。")
        return False