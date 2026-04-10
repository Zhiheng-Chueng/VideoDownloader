import customtkinter as ctk
import threading
import os
from core.manager import DownloadManager

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("多平台视频下载器 (格式选择版)")
        self.geometry("700x600")
        
        self.manager = DownloadManager()
        self.save_dir = "downloads"
        os.makedirs(self.save_dir, exist_ok=True)
        self.current_url = ""
        self.selected_format = ctk.StringVar(value="best") # 默认值为 best

        self.setup_ui()

    def setup_ui(self):
        # 1. 顶部输入与解析区域
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="x")
        
        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="输入视频链接...", height=40)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.parse_btn = ctk.CTkButton(self.input_frame, text="1. 解析链接", height=40, command=self.on_parse_click)
        self.parse_btn.pack(side="right")

        # 2. 中间动态选项区域 (带滚动条)
        self.options_frame = ctk.CTkScrollableFrame(self, label_text="2. 选择下载格式 (请先解析)")
        self.options_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # 3. 底部操作与日志区域
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=10, padx=20, fill="x")

        self.download_btn = ctk.CTkButton(self.bottom_frame, text="3. 开始下载", height=40, state="disabled", command=self.on_download_click)
        self.download_btn.pack(side="top", fill="x", pady=(0, 10))

        self.log_box = ctk.CTkTextbox(self.bottom_frame, height=150, state="disabled", font=("Consolas", 12))
        self.log_box.pack(side="bottom", fill="both", expand=True)

    def log_to_ui(self, message):
        def update():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, update)

    # ================= 解析流程 =================
    def on_parse_click(self):
        url = self.url_entry.get().strip()
        if not url: return
        
        self.current_url = url
        self.parse_btn.configure(state="disabled", text="解析中...")
        self.log_to_ui(f"--- 开始解析: {url} ---")
        
        # 清空之前的选项
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        threading.Thread(target=self.run_parse, args=(url,), daemon=True).start()

    def run_parse(self, url):
        info = self.manager.get_info(url)
        self.after(0, self.update_options_ui, info)

    def update_options_ui(self, info):
        self.parse_btn.configure(state="normal", text="1. 重新解析")
        if not info or 'formats' not in info:
            self.log_to_ui("❌ 解析失败或未找到格式信息。")
            return
            
        self.log_to_ui("✅ 解析成功！请在上方选择格式。")
        self.options_frame.configure(label_text=f"视频: {info.get('title', '未知标题')}")

        # 默认提供最佳选项
        ctk.CTkRadioButton(self.options_frame, text="最佳音视频合并 (Best)", variable=self.selected_format, value="best").pack(anchor="w", pady=5)

        # 提取视频流 (有画面)
        ctk.CTkLabel(self.options_frame, text="▶ 视频格式 (可能需要FFmpeg合并音频):", text_color="gray").pack(anchor="w", pady=(10, 0))
        for f in info['formats']:
            if f.get('vcodec') != 'none': # 有画面
                res = f.get('resolution', '未知分辨率')
                ext = f.get('ext', 'mp4')
                note = f.get('format_note', '')
                fid = f.get('format_id', '')
                # 如果既有视频又有音频，使用 {fid}；如果只有视频，通常需要配合最佳音频 bestaudio 下载，yt-dlp 语法为 {fid}+bestaudio
                dl_id = fid if f.get('acodec') != 'none' else f"{fid}+bestaudio"
                text = f"[{ext}] {res} {note} (ID: {fid})"
                ctk.CTkRadioButton(self.options_frame, text=text, variable=self.selected_format, value=dl_id).pack(anchor="w", pady=2, padx=10)

        # 提取纯音频流
        ctk.CTkLabel(self.options_frame, text="🎵 纯音频格式:", text_color="gray").pack(anchor="w", pady=(10, 0))
        for f in info['formats']:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                abr = f.get('abr', '未知')
                ext = f.get('ext', 'm4a')
                fid = f.get('format_id', '')
                text = f"[{ext}] 音频码率: {abr}kbps (ID: {fid})"
                ctk.CTkRadioButton(self.options_frame, text=text, variable=self.selected_format, value=fid).pack(anchor="w", pady=2, padx=10)

        # 启用下载按钮
        self.download_btn.configure(state="normal")

    # ================= 下载流程 =================
    def on_download_click(self):
        fid = self.selected_format.get()
        self.download_btn.configure(state="disabled", text="下载中...")
        self.log_to_ui(f"\n--- 开始执行下载任务 (参数: {fid}) ---")
        
        threading.Thread(target=self.run_download, args=(self.current_url, fid), daemon=True).start()

    def run_download(self, url, fid):
        self.manager.start_download(url, self.save_dir, fid, self.log_to_ui)
        self.after(0, lambda: self.download_btn.configure(state="normal", text="3. 开始下载"))

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    app = App()
    app.mainloop()