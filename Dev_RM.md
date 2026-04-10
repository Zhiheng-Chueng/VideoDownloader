VideoDownloader 项目架构手册 (V1.0)1. 项目愿景构建一个插件化、高容错、全平台的视频下载框架。核心理念是“调度与实现分离”：由管理器负责匹配 URL，由具体的 Handler 负责执行下载。2. 核心架构设计 (Architecture Overview)2.1 模块职责划分模块名称核心职责依赖关系Main (Entry)程序的启动入口，负责初始化环境和注册插件。依赖 Core.ManagerManager (Brain)维护处理器队列，执行 URL 路由匹配和异常重试逻辑。依赖 Core.BaseHandlerHandlers (Workers)BaseHandler: 定义接口契约。YTDLP: 通用解析引擎。Custom: 针对特定站点的硬核解析。继承 BaseHandlerUtils (Tools)提供日志记录、文件路径处理、FFmpeg 校验等通用工具。无依赖2.2 设计模式策略模式 (Strategy Pattern): 每一个 Handler 都是一种下载策略，系统根据 URL 特征动态选择策略。外观模式 (Facade Pattern): DownloadManager 为上层 UI 提供统一的 start_download 接口，隐藏底层复杂的解析细节。3. 核心对象协议 (Interface Contract)任何接入本系统的 AI 必须遵循以下 BaseHandler 的接口定义：Pythonclass BaseHandler:
    def can_handle(self, url: str) -> bool:
        """
        逻辑：通过正则表达式匹配 URL。
        返回：True (接管任务) / False (跳过)
        """
        pass

    def download(self, url: str, save_path: str):
        """
        逻辑：具体的下载实现（如调用 subprocess 或 Requests）。
        要求：必须捕获自身异常并向上抛出标准错误流。
        """
        pass
4. 扩展流程 (How to Extend)场景 A：新增一个特殊加密站点的下载在 handlers/ 下创建 site_xxx_handler.py。继承 BaseHandler 并实现私有解析逻辑。在 main.py 中使用 manager.register_handler(SiteXXXHandler()) 进行注册。注意：自定义 Handlers 的注册优先级应高于 YTDLPHandler（通用垫底）。场景 B：接入 GUI 界面GUI 实例化 DownloadManager。将 DownloadManager.start_download 放入独立线程（或使用 Python 的 threading/asyncio）以防 UI 假死。通过自定义 Callback 函数将 subprocess 的进度流实时传递给 UI。5. 环境约束 (Environment)Runtime: Python 3.10+Binary Dependency:./bin/ffmpeg: 负责音视频合并。./bin/yt-dlp: 负责通用站点解析。Path Logic: 优先使用相对路径访问 bin/ 目录下的二进制文件，确保软件的便携性（Portable）。6. AI 协作指令 (Prompt for AI)“你现在是一名高级 Python 开发人员。请基于 BaseHandler 类，为我编写一个针对 [站点名] 的 CustomHandler。要求：使用正则表达式在 can_handle 中进行严格匹配。在 download 方法中，如果需要调用系统内的 ffmpeg，请指向 ./bin/ffmpeg。保持代码的模块化，不要修改 core/ 目录下的底层逻辑。”