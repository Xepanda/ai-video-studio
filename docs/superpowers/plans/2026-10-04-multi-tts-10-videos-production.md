# Multi-TTS Open-Source Engine & 10+ Long-Form (2min+) Video Production Implementation Plan

> **Goal**: Deploy and test 4 open-source local TTS engines (GPT-SoVITS, ChatTTS, Kokoro-82M, F5-TTS), assign diverse wiki topics, generate at least 10 polished videos (each >= 2 minutes / 120s), polish the entire Remotion & alignment pipeline, and iterate workflow documentation and skills.

---

## 1. Production Matrix (10+ Videos, >= 2 Minutes Each)

| # | Video Title & Wiki Topic | Engine | Voice Style / Character | Target Duration | Output File |
|---|--------------------------|--------|-------------------------|-----------------|-------------|
| **01** | AI 音视频架构与硬件抉择 (`01-audio-and-video-architecture.mdx`) | **GPT-SoVITS** | 社区模型：鸣潮守岸人 (知性清冷) | >= 120s (~10分镜) | `out/01_audio_video_architecture_sovits.mp4` |
| **02** | 嵌入式电机 FOC 控制实战 (`hardware-embedded/motor-foc`) | **GPT-SoVITS** | 社区模型：亚瑟摩根 (深沉磁性) | >= 120s (~10分镜) | `out/02_motor_foc_sovits.mp4` |
| **03** | 个人 IP 专属声音克隆之路 (`06-personal-voice-cloning.mdx`) | **GPT-SoVITS** | 个人克隆权重 (`epanda_voice`) | >= 120s (~10分镜) | `out/03_personal_voice_cloning_sovits.mp4` |
| **04** | Cloudflare 生态与边缘计算实战 (`cloud-and-edge/01-cloudflare`) | **ChatTTS** | Seed A：极客日常闲聊 (带笑声/口语) | >= 120s (~11分镜) | `out/04_cloudflare_ecosystem_chattts.mp4` |
| **05** | 泰山派开发板与家庭 NAS 搭建 (`taishanpi/07-nas-storage`) | **ChatTTS** | Seed B：生活化科技畅聊 (松弛感) | >= 120s (~11分镜) | `out/05_taishanpi_nas_chattts.mp4` |
| **06** | 三大 AI 视频制作流深度横评 (`02-three-video-production-pipelines`) | **ChatTTS** | Seed C：青年极客快节奏解说 | >= 120s (~11分镜) | `out/06_three_video_pipelines_chattts.mp4` |
| **07** | Transformer 深度案例剖析 (`03-flagship-transformer-case-study`) | **Kokoro-82M** | 现代清爽科技男声 (清晰圆润) | >= 120s (~12分镜) | `out/07_transformer_case_study_kokoro.mp4` |
| **08** | Google AI 视频生态与前沿技术 (`04-google-ai-video-ecosystem`) | **Kokoro-82M** | 现代知性科技女声 (播客质感) | >= 120s (~12分镜) | `out/08_google_ai_video_kokoro.mp4` |
| **09** | AI Video Studio 全自动化流水线详解 (`05-ai-video-studio`) | **Kokoro-82M** | 双语极客混读声线 (圆润自然) | >= 120s (~12分镜) | `out/09_studio_workflow_deepdive_kokoro.mp4` |
| **10** | 影视级音视频后期渲染与流匹配 (`remotion-edge-tts-pipeline`) | **F5-TTS** | 电影级沉稳旁白男声 (Diffusion DiT) | >= 120s (~10分镜) | `out/10_remotion_flow_matching_f5tts.mp4` |
| **11** | 硬件到云端的全栈思考与极客工作流 | **Edge-TTS (对比)** | 云扬专业播报男声 (基准参照组) | >= 120s (~10分镜) | `out/11_fullstack_hardware_cloud_edge.mp4` |

---

## 2. Technical Roadmap & Pipeline Tasks

### Phase 1: TTS Engine Standup & Adapters
- [ ] Task 1.1: Download & configure GPT-SoVITS community character weights from ModelScope (`Shorekeeper`, `Arthur Morgan`).
- [ ] Task 1.2: Install and configure `ChatTTS` with ModelScope weights and build standalone synthesis module `scripts/tts_chattts.py`.
- [ ] Task 1.3: Deploy `Kokoro-82M` via `kokoro-onnx` and ModelScope weights, build `scripts/tts_kokoro.py`.
- [ ] Task 1.4: Install & test `F5-TTS` (or flow-matching fallback with DiT weights) in `scripts/tts_f5tts.py`.
- [ ] Task 1.5: Update `generate_audio.py` to support unified `--provider` selection across all 4 engines.

### Phase 2: Long-Form (2min+) Script Generation
- [ ] Task 2.1: Extract substantive technical content from `D:\Projects\wiki\docs`.
- [ ] Task 2.2: Author 11 rich, multi-scene scripts (10~14 scenes each, spoken word count ~450-650 words each) ensuring >= 120 seconds duration.
- [ ] Task 2.3: Validate script schema compliance.

### Phase 3: Batch Audio Synthesis & Forced Alignment
- [ ] Task 3.1: Generate audio for Videos 01-03 using GPT-SoVITS engines.
- [ ] Task 3.2: Generate audio for Videos 04-06 using ChatTTS engines.
- [ ] Task 3.3: Generate audio for Videos 07-09 using Kokoro-82M engines.
- [ ] Task 3.4: Generate audio for Video 10 using F5-TTS, and Video 11 using Edge-TTS reference.
- [ ] Task 3.5: Run SenseVoice forced alignment for all 11 video timelines.

### Phase 4: Remotion Visual Templating & Video Rendering
- [ ] Task 4.1: Ensure Remotion components support dynamic duration and rich scene transitions across 10-14 scenes per composition.
- [ ] Task 4.2: Render all 11 videos in 1080p 60fps.
- [ ] Task 4.3: Verify each video duration is >= 120 seconds (7200 frames).

### Phase 5: Workflow, Skill & Wiki Polish
- [ ] Task 5.1: Create/update video production skills for multi-engine orchestration.
- [ ] Task 5.2: Update Wiki documentation with the comprehensive Multi-TTS Benchmark report.
- [ ] Task 5.3: Commit changes to Git repositories.
