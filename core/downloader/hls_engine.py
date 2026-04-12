import os
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class HLSEngine:
    def __init__(self, session, max_workers=10):
        self.session = session
        self.max_workers = max_workers
        self.key_cache = {}

    def download_all(self, segments, base_url, temp_dir, log_callback=None):
        """核心：并发下载并解密所有切片"""
        total = len(segments)
        # 预先生成所有任务参数
        tasks = []
        for idx, seg in enumerate(segments):
            ts_url = seg.absolute_uri or urljoin(base_url, seg.uri)
            tasks.append((idx, ts_url, seg))

        def _worker(task):
            idx, ts_url, seg = task
            try:
                res = self.session.get(ts_url, timeout=20)
                if res.status_code != 200: return False
                
                data = res.content
                # 实时解密逻辑
                if seg.key and seg.key.method == 'AES-128':
                    data = self._decrypt(data, seg, base_url)
                
                # 写入独立小文件，避免多线程写入冲突
                part_path = os.path.join(temp_dir, f"{idx:05d}.ts")
                with open(part_path, 'wb') as f:
                    f.write(data)
                return True
            except Exception as e:
                if log_callback: log_callback(f"❌ 分片 {idx} 失败: {str(e)}")
                return False

        # 启动线程池突击
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(_worker, tasks))
        
        return all(results)

    def _decrypt(self, data, seg, base_url):
        """解密工具私有化"""
        k_uri = seg.key.absolute_uri or urljoin(base_url, seg.key.uri)
        if k_uri not in self.key_cache:
            k_res = self.session.get(k_uri, timeout=10)
            self.key_cache[k_uri] = k_res.content
        
        key = self.key_cache[k_uri]
        iv = bytes.fromhex(seg.key.iv.replace('0x', '')) if seg.key.iv else \
             (seg.media_sequence or 0).to_bytes(16, 'big') # 简版逻辑
             
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()