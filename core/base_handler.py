from abc import ABC, abstractmethod

class BaseHandler(ABC):
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        pass

    @abstractmethod
    def get_info(self, url: str) -> dict | None:
        """新增：获取视频元数据信息"""
        pass

    @abstractmethod
    def download(self, url: str, save_path: str, format_id: str = "best", log_callback=None) -> bool:
        """修改：增加 format_id 参数"""
        pass