from .ytdlp_handler import YTDLPHandler

class DownloadManager:
    def __init__(self):
        self.handlers = []
        self.register_handler(YTDLPHandler())

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