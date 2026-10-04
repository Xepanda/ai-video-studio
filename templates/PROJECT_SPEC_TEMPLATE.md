# 📋 视频项目制作规格与分镜需求表 (Project Spec Template)

> **使用说明**：制作新视频时，请复制此模板并填写各分镜内容。AI 编码系统将根据此文档自动驱动 **TTS 声音克隆 ➔ SenseVoice 毫秒打点 ➔ Remotion 组件光栅化渲染** 全流程。

---

## 1. 项目基础信息

| 字段 | 必填 | 示例 / 说明 | 你的填写 |
| :--- | :---: | :--- | :--- |
| **项目标识 (Project ID)** | 是 | `docker_architecture_01`（英文字母/下划线） |  |
| **视频标题 (Title)** | 是 | 《3分钟彻底搞懂 Docker 容器核心原理》 |  |
| **画面画幅 (Aspect Ratio)** | 是 | `16:9` (1920x1080) 或 `9:16` (1080x1920) |  |
| **帧率 (FPS)** | 是 | 默认 `30` |  |
| **主视频形态 (Primary Mode)** | 是 | `Explainer` (科普) / `Shorts` (自媒体) / `HandsOn` (实战) / `Hybrid` (混剪) |  |
| **预估总时长** | 否 | 约 60 秒 ~ 180 秒 |  |

---

## 2. 声音与配音配置

* **配音方案**：
  - [ ] 个人音色克隆（GPT-SoVITS 专属模型）
  - [ ] 零样本音色克隆（提供 `models/reference_audio/my_voice.wav`）
  - [ ] 手动录制原声干声（直接提供已录好的 WAV 文件放至 `public/audio/`）
* **发音语速**：`1.0x`（正常） / `1.15x`（高节奏短视频）
* **全局主基调**：沉稳技术流 / 幽默风趣 / 激情短视频

---

## 3. 视觉规范与主题调色

* **调色预设**：
  - [ ] `Dark Geek`（深色极客蓝黑 `#090d16`，代码/芯片专用）
  - [ ] `Whiteboard Clean`（象牙白手绘纸质 `#fcfaf2`，科普专用）
  - [ ] `Warm Editorial`（暖色质感自媒体，小红书/B站生活流）
  - [ ] `Cyber Glow`（赛博霓虹流光，硬件/动效专用）
* **品牌强调色 (Accent Color)**：`#38bdf8` (科技天蓝) / `#10b981` (终端翠绿) / `#f59e0b` (告警亮橙)

---

## 4. 逐分镜详细设计表 (Scene Storyboard)

> **每个分镜独立成块**。音频生成后，系统会自动根据 ASR 毫秒打点决定该分镜在 Remotion 中的精确总帧数。

---

### 分镜 1：开门见山 / 痛点引入
* **分镜 ID**：`scene_01`
* **分镜形态**：`ExplainerWhiteboard`（白板手绘）
* **旁白台词 (Narration)**：
  > “你是不是也遇到过这种情况：在自己电脑上跑得好好的代码，一发给同事，就彻底崩溃了？”
* **画面核心呈现**：
  * 左侧展示开发者电脑与开心表情，右侧展示同事电脑与巨大红色报错图标（`Error 404 / Crash`）。
  * 中间出现一道裂缝与问号。
* **动效与交互要求**：
  * 报错图标伴随物理弹簧阻尼入场；
  * 词级高亮：“跑得好好的代码”（变绿）、“彻底崩溃了”（变红闪烁）。
* **外部素材 / B-Roll 需求**：
  * [ ] 无，纯程序化 SVG 绘制
  * [ ] 实拍/录屏：`public/footage/xxxx.mp4`
  * [ ] **Google Flow AI 生成视频**（见下方 Prompt）
    * **提示词 (Prompt)**：`Cinematic close-up of a glowing retro computer screen displaying rapid cascading red error code in a dark cyberpunk room, 4k, smooth camera push-in`
    * **目标落盘文件名**：`public/footage/broll_scene_01.mp4`

---

### 分镜 2：核心原理解析
* **分镜 ID**：`scene_02`
* **分镜形态**：`TerminalCodeDemo`（终端实战）
* **旁白台词 (Narration)**：
  > “Docker 的解决思路极其简单：它把代码连同所有依赖环境，打包塞进一个独立的集装箱里。”
* **画面核心呈现**：
  * 终端敲入命令 `docker run -d -p 80:80 my-app:latest`；
  * 旁边由点阵图标转换出的矢量 Docker 鲸鱼 Logo 动态描边入场（`pixel2motion`）；
  * 架构图弹簧展示“应用 + 依赖 + 运行时”三合一封装卡片。
* **动效与交互要求**：
  * 打字机速度与语速“敲入命令”毫秒对齐；
  * 命令执行完成后输出绿色的 `[OK] Container started`。
* **外部素材 / B-Roll 需求**：
  * 无

---

### 分镜 3：实拍混剪 / 硬件联动（如适用）
* **分镜 ID**：`scene_03`
* **分镜形态**：`RealVideoHybrid`（实拍画中画 + 激光指针）
* **旁白台词 (Narration)**：
  > “我们现在把这个容器镜像，直接烧录进这块手掌大小的微型开发板中。”
* **画面核心呈现**：
  * 实拍手机录制视频：开发板实物特写。
  * 画面上包裹 3D 浮动金属圆角画中画外壳。
  * 动态发光指示线（Callout Pointer）从画面右侧伸出，精确指引在开发板的 CPU 核心芯片上。
* **外部素材 / B-Roll 需求**：
  * [x] 实拍原片：`public/footage/esp32_board_shot.mp4`

---

## 5. 提交前自检清单 (Pre-Flight Check)

在把本需求表交付系统制作前，请确认：
- [ ] 旁白台词中无容易产生歧义的多音字（如：`银行` vs `行业`，建议注音为 `yín háng` 或 `háng yè`）；
- [ ] 所有引用到的实拍视频（MP4/MOV）已拷贝至 `public/footage/`；
- [ ] 如果规划了 Google Flow 视频，已在 [flow.google.com](https://flow.google.com/) 生成下载并按约定名称保存至 `public/footage/`；
- [ ] 确认画面画幅（横屏 16:9 / 竖屏 9:16）符合发布平台规范。
