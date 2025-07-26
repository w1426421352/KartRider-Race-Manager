
# 跑跑卡丁车赛事管理器 (KartRider Race Manager)

![Project Banner](https://placehold.co/1200x300/4A90E2/FFFFFF?text=KartRider%20Race%20Manager&font=sans)

一款专为《跑跑卡丁车》设计的专业级竞赛管理平台，旨在通过自动化、专业化、趣味化的方式，为赛事组织者（桌面端）和参赛选手（Web端）提供一站式解决方案。

> **重要声明**: 本项目的大部分代码及本文档均由大型语言模型（AI）根据项目设计文档生成，旨在探索AI辅助软件开发的潜力。代码可能存在潜在的错误或未优化的部分，欢迎社区共同参与改进。

---

## ✨ 核心功能

本平台同时服务于两大核心用户群体：**赛事组织者 (管理员)** 和 **参赛选手 (玩家)**。

#### 为赛事组织者 (管理员):

  * **智能地图库管理**:

      * **全自动扫描与导入**: 自动发现游戏客户端，一键调用原生C\#解包工具 (`RhoUnpacker.exe`)，从`track_common.rho`、`trackThumb.rho`和`dialog2_selectTrackEx.rho`中目标性解包并导入完整的地图数据。
      * **原生BML解析**: 程序内置纯Python实现的`.bml`解析器，可直接读取游戏二进制XML文件，提取地图元数据。
      * **多语言数据聚合**: 自动整合各地区客户端的地图译名（简中、繁中、韩语等），实现国际化展示。
      * **双视图浏览**: 提供直观的“卡片网格”与用于批量编辑的“数据表格”两种浏览模式，并可一键切换。
      * **强大筛选系统**: 支持按主题、名称/ID搜索、游戏类型及高级自定义条件（如“缺少某语言译名”）进行复合筛选。
      * **持久化地图池**: 通过复选框自由勾选地图组成赛事专用图池，选择状态会自动存入数据库。
      * **赛事图片一键生成**: 将自定义的地图池（含缩略图、多语言名称、难度等）一键导出为按主题分组、排版精美的赛事公告图。

  * **可视化规则集编辑器 (开发中)**:

      * 通过图形化“积木式”表单，直观地创建和管理包含复杂逻辑（如IF-THEN-ELSE）的比赛规则。
      * 支持跨规则集拖拽、复制规则，极大提升赛事配置效率。

  * **Web端选手门户 (规划中)**:

      * 选手可通过网页实时查看比赛信息、地图池及个人战绩。
      * 内置安全的会话令牌机制，完美兼容`frp`等内网穿透工具，适应复杂网络环境。

  * **安全认证系统**:

      * 采用业界标准的`PBKDF2`算法加盐哈希，安全存储用户密码。
      * 严格的字符集验证，从源头杜绝潜在的数据风险。

#### 为参赛选手 (玩家):

  * **便捷的登录方式**: 支持账号密码、临时密码及一键扫码安全登录。
  * **实时信息获取**: 在个人仪表盘上实时查看自己的比分、排名和当前比赛状态。
  * **深度的赛事互动**: 根据管理员设定的规则，在网页端直接参与地图投票、选择等互动环节。

## 🛠️ 技术架构

  * **主体语言**: `Python`
  * **桌面端 GUI**: `PyQt6` (纯代码编写，以实现高度定制化界面)
  * **核心后端服务**:
      * **Web 框架**: `FastAPI`
      * **实时通信**: `WebSockets`
  * **数据库**: `SQLite` (主数据库) + `JSON` (配置文件与数据交换)
  * **外部工具链**:
      * **解包器**: 使用 **`.NET 8 Native AOT`** 编译的 `RhoUnpacker.exe`，实现高效、无.NET环境依赖的游戏文件解包。
  * **关键第三方库**: `Pillow`, `BeautifulSoup4`, `lxml`, `asteval`

## 📂 项目结构

```

kart_counter/
├── core/                # 核心后端逻辑 (UI无关)
│   ├── auth_manager.py
│   ├── bml_parser.py
│   ├── db_manager.py
│   └── map_manager.py
├── ui/                  # 所有桌面端UI代码
│   └── views/
│       └── map_manager/ # 地图管理模块UI
├── web/                 # Web端服务代码
├── tools/               # 外部工具链 (如 RhoUnpacker.exe)
├── assets/              # 静态资源 (图标、字体等)
└── main.py              # 程序主入口

````

## 🚀 快速开始

### 1. 环境要求
- Python 3.9-3.11（推荐使用3.11）
- Windows 操作系统
- 已安装的《跑跑卡丁车》游戏客户端

### 2. 安装依赖
```bash
# 建议在虚拟环境中操作
pip install -r requirements.txt
````


### 3\. 运行程序

```bash
python main.py
```

### 4\. 使用说明

1.  首次启动，程序会自动在 `data/` 目录下初始化数据库。
2.  进入“地图库管理”模块，点击“扫描游戏”按钮。
3.  程序将自动查找游戏路径及解包工具，若查找失败，会提示您手动指定。
4.  确认后，程序将在后台自动完成解包、数据聚合、图片缓存等所有流程。
5.  流程结束后，您即可在界面中浏览、筛选和导出地图。

## 展望未来

我们的下一个核心开发目标是：**实现“规则集可视化编辑器”的完整功能**。

该模块将连接强大的UI原型与后端的`core/rule_engine.py`服务，让用户能真正通过图形界面创建和管理驱动比赛的灵魂——规则集。

## 🙏 致谢 (Acknowledgements)

本项目的开发受到了以下优秀开源项目的启发和帮助，在此表示衷心的感谢：

**项目灵感与参考:**

  - [Aaron001222/KartRider-Score-V0.2](https://github.com/Aaron001222/KartRider-Score-V0.2)
  - [lansdarklauh/Teager-Competition-Assistant](https://github.com/lansdarklauh/Teager-Competition-Assistant)

**核心工具来源:**

  - **游戏文件解包器 (`RhoUnpacker`)**:
      - **核心算法原作者**: [xpoi5010/Kartrider-File-Reader](https://github.com/xpoi5010/Kartrider-File-Reader)
      - **使用的 Fork**: [yanygm/Kartrider-File-Reader (fork)](https://github.com/yanygm/Kartrider-File-Reader)
      - **本项目使用的 AI 修改版**: [w1426421352/RhoUnpacker](https://github.com/w1426421352/RhoUnpacker)

## 📄 许可证

本项目基于 **MIT 许可证** 开源。详情请见 [LICENSE](https://www.google.com/search?q=LICENSE) 文件。

-----

*本项目由在 AI 的协助下创建。*
