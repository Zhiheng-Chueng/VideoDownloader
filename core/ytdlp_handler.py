import subprocess
import os
import json
from .base_handler import BaseHandler

class YTDLPHandler(BaseHandler):
    def __init__(self):
        ext = ".exe" if os.name == "nt" else ""
        self.ytdlp_path = os.path.join("bin", f"yt-dlp{ext}")
        self.ffmpeg_path = os.path.join("bin", f"ffmpeg{ext}")

    def can_handle(self, url: str) -> bool:
        return True

    def get_info(self, url: str) -> dict | None:
        """新增：静默获取视频全部格式信息"""
        cmd = [self.ytdlp_path, "-J", "--no-warnings", url]
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            # 阻塞式获取 JSON，由于我们会在主程序开子线程，所以不会卡死
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                text=True, creationflags=creationflags, encoding='GB18030'
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception as e:
            print(f"解析失败: {e}")
            return None

    def download(self, url: str, save_path: str, format_id: str = "best", log_callback=None) -> bool:
        def log(msg):
            if log_callback: log_callback(msg)

        if not os.path.exists(self.ytdlp_path):
            log(f"❌ 错误: 找不到 {self.ytdlp_path}")
            return False

        # 修改：加入了 -f {format_id} 参数
        cmd = [
            self.ytdlp_path,
            url,
            "-f", format_id,
            "-o", os.path.join(save_path, "%(title)s.%(ext)s"),
            "--ffmpeg-location", self.ffmpeg_path,
            "--no-mtime",
            "--newline" 
        ]
        
        log(f"🚀 开始下载格式 [{format_id}]...")
        
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, creationflags=creationflags, encoding='GB18030'
            )

            for line in process.stdout:
                log(line.strip())
            
            process.wait()
            return process.returncode == 0
        except Exception as e:
            log(f"❌ 异常: {str(e)}")
            return False