import os
import subprocess
import requests
import m3u8
from urllib.parse import urljoin, urlparse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class GenericHLSHandler:
    def __init__(self):
        ext = ".exe" if os.name == "nt" else ""
        self.ffmpeg_path = os.path.join("bin", f"ffmpeg{ext}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        })

    def can_handle(self, url: str) -> bool:
        return ".m3u8" in url or "hls" in url.lower()

    def get_info(self, url: str) -> dict | None:
        return {
            'title': 'HLS_Stream_Video',
            'formats': [{'format_id': 'hls_custom', 'ext': 'mp4', 'resolution': 'auto'}]
        }

    def download(self, url: str, save_path: str, format_id: str = "best", log_callback=None) -> bool:
        def log(msg):
            if log_callback: log_callback(msg)

    # 1. 动态伪装 (如果 main.py 没传，我们就用当前 m3u8 域名保底)
        if 'Referer' not in self.session.headers:
            from urllib.parse import urlparse
            domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
            self.session.headers.update({'Referer': domain})

        # 2. 检查 User-Agent 是否与解析时完全一致
        # (这步依赖于你在 main.py 里同步过来的 headers)
        log(f"🕵️ 伪装 UA: {self.session.headers.get('User-Agent')[:50]}...")

        temp_ts_path = os.path.join(save_path, f"temp_{format_id}.ts")
        final_mp4_path = os.path.join(save_path, f"Video_{format_id}.mp4")

        try:
            log(f"🔗 正在请求加密索引...")
            # 注意：这里也需要带上 headers，否则取不到正确的 m3u8
            res = self.session.get(url, timeout=10)
            
            # --- 输出反馈：如果 M3U8 都拿不到，直接看 Header ---
            if res.status_code != 200:
                log(f"❌ 索引获取失败! Code: {res.status_code}")
                log(f"⚠️ 此时 Session 中的 Cookies: {self.session.cookies.get_dict()}")
                return False

            playlist = m3u8.loads(res.text, uri=url)
            # ... 后续循环下载逻辑保持不变 ...
            
            if not playlist.segments:
                log("⚠️ 警告: 该 M3U8 是 Master Playlist，请使用包含分辨率的子链接。")
                return False

            total = len(playlist.segments)
            log(f"📦 解析成功: 共 {total} 个切片")
            key_cache = {}

            with open(temp_ts_path, 'wb') as f:
                for idx, seg in enumerate(playlist.segments):
                    ts_url = seg.absolute_uri or urljoin(url, seg.uri)
                    
                    # --- 侦察阶段 2: 下载切片 ---
                    ts_res = self.session.get(ts_url, timeout=15)
                    if ts_res.status_code != 200:
                        log(f"❌ 切片 {idx} 拿不到 (Code: {ts_res.status_code})")
                        log(f"🔗 失败地址: {ts_url}")
                        return False

                    data = ts_res.content

                    # --- 侦察阶段 3: 硬核解密审计 ---
                    if seg.key and seg.key.method == 'AES-128':
                        k_uri = seg.key.absolute_uri or urljoin(url, seg.key.uri)
                        if k_uri not in key_cache:
                            k_res = self.session.get(k_uri, timeout=10)
                            if k_res.status_code != 200:
                                log(f"❌ 密钥下载失败! Code: {k_res.status_code}")
                                return False
                            key_cache[k_uri] = k_res.content
                            log(f"🔑 成功获取密钥: {key_cache[k_uri].hex()[:16]}...")

                        key = key_cache[k_uri]
                        # 确定 IV
                        if seg.key.iv:
                            iv = bytes.fromhex(seg.key.iv.replace('0x', ''))
                        else:
                            # 基于序列号生成 IV
                            seq = playlist.media_sequence + idx if playlist.media_sequence else idx
                            iv = seq.to_bytes(16, 'big')
                        
                        if idx == 0: log(f"🛠️ 解密参数: IV={iv.hex()}, KeyLen={len(key)}")

                        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                        decryptor = cipher.decryptor()
                        data = decryptor.update(data) + decryptor.finalize()

                    # --- 侦察阶段 4: 数据完整性探针 ---
                    if idx == 0:
                        if data.startswith(b'G'): # 0x47 的 ASCII 是 'G'
                            log("✅ 探针结果: 解密后数据以 0x47 开头，结构正常。")
                        else:
                            log(f"⚠️ 探针警报: 数据头为 {data[:4].hex()}，非标准 TS 流，播放可能黑屏。")

                    f.write(data)
                    if (idx + 1) % 10 == 0 or (idx + 1) == total:
                        log(f"🚀 处理中: {idx+1}/{total}")

            # --- 侦察阶段 5: FFmpeg 封口 ---
            log("🎬 正在执行 [全量流修复] 与 [索引重构]...")
        
            cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", temp_ts_path,
            "-c:v", "libx264",       # 强制重写视频流，解决画面黑屏/乱序
            "-preset", "ultrafast",  # 使用最快预设，减少 CPU 负担，适合图书馆环境
            "-crf", "23",            # 兼顾清晰度和文件大小
            "-c:a", "aac",           # 强制重写音频流
            "-bsf:a", "aac_adtstoasc",
            "-vsync", "1",           # 强制帧同步，防止音画不同步
            "-avoid_negative_ts", "make_zero", # 确保视频从 00:00 开始
            final_mp4_path
            ]
            p = subprocess.run(cmd, capture_output=True, creationflags=0x08000000 if os.name == 'nt' else 0)
            
            if p.returncode == 0:
                log(f"✨ 完工! 文件: {final_mp4_path}")
                os.remove(temp_ts_path)
                return True
            else:
                log(f"❌ FFmpeg 报错: {p.stderr.decode(errors='ignore')[:100]}")
                return False

        except Exception as e:
            log(f"💥 崩溃分析: {str(e)}")
            return False