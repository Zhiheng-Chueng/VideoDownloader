import os
import socket
import qrcode
import threading
import sys
import time
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# 配置文件名和路径
DOWNLOAD_FOLDER = "downloads"
PORT = 8000  # 临时服务器端口
QR_IMAGE_NAME = "scan_to_download.png"

def get_local_ip():
    """
    获取本机在局域网中的IP地址。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 不需要真的连接，只需以此获取本机接口IP
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_server(path_to_serve, port):
    """
    在指定目录启动 HTTP 服务器。
    """
    # 切换到 download 目录，这样下载链接就是 /文件名
    os.chdir(path_to_serve)
    
    handler = SimpleHTTPRequestHandler
    # 允许端口重用，防止脚本重启时报错
    TCPServer.allow_reuse_address = True
    
    with TCPServer(("", port), handler) as httpd:
        print(f"\n[🚀 服务器] 局域网共享已启动，端口: {port}")
        print(f"[📂 目录] 正在共享: {os.getcwd()}")
        print("[ℹ️ 提示] 手机下载完成后，在电脑终端按 Ctrl+C 停止服务器。")
        httpd.serve_forever()

def generate_qr_code(data):
    """
    根据数据生成二维码并在终端显示（如果支持），同时保存为图片。
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # 保存为图片
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(QR_IMAGE_NAME)
    print(f"\n[🖼️ 二维码] 已保存为 '{QR_IMAGE_NAME}'，请用手机扫描。")

    # 尝试在终端打印二维码 (需要终端支持，通常 Linux/macOS 支持较好，Windows 10+ 也可)
    try:
        qr.print_ascii(invert=True)
    except Exception:
        pass # 如果终端不支持打印，跳过

def main():
    # 1. 确认 download 文件夹存在
    project_root = os.getcwd()
    download_path = os.path.join(project_root, DOWNLOAD_FOLDER)
    
    if not os.path.exists(download_path):
        print(f"❌ 错误: 找不到 '{DOWNLOAD_FOLDER}' 文件夹。")
        return

    # 2. 列出并选择视频文件
    # 支持的视频格式，可自行添加
    video_extensions = ('.mp4', '.mkv', '.avi', '.flv', '.mov')
    files = [f for f in os.listdir(download_path) if f.lower().endswith(video_extensions)]
    
    if not files:
        print(f"👻 '{DOWNLOAD_FOLDER}' 文件夹中没有找到视频文件。")
        return

    print("\n--- 📝 download 文件夹中的视频列表 ---")
    for i, file in enumerate(files):
        print(f"[{i + 1}] {file}")
    print("---------------------------------------")

    try:
        choice = int(input(f"\n请输入要分享的视频编号 (1-{len(files)}): "))
        if 1 <= choice <= len(files):
            selected_file = files[choice - 1]
        else:
            print("❌ 输入错误。")
            return
    except ValueError:
        print("❌ 请输入数字。")
        return

    # 3. 构建局域网下载 URL
    local_ip = get_local_ip()
    # 对文件名进行 URL 编码，防止空格或中文导致链接失效
    from urllib.parse import quote
    encoded_filename = quote(selected_file)
    download_url = f"http://{local_ip}:{PORT}/{encoded_filename}"
    
    print(f"\n[✅ 已选择] {selected_file}")
    print(f"[🔗 下载链接] {download_url}")

    # 4. 生成二维码
    generate_qr_code(download_url)

    # 5. 在主线程中启动服务器，拦截 Ctrl+C
    try:
        # 注意：这里需要传入完整路径，因为 start_server 会用 chdir 切换过去
        start_server(download_path, PORT)
    except KeyboardInterrupt:
        print("\n\n[🛑 服务器] 已由用户停止。")
        # 清理生成的二维码图片
        if os.path.exists(os.path.join(project_root, QR_IMAGE_NAME)):
            try:
                os.remove(os.path.join(project_root, QR_IMAGE_NAME))
                print(f"[🧹 清理] 已删除临时二维码图片。")
            except Exception as e:
                print(f"[⚠️ 警告] 删除二维码图片失败: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()