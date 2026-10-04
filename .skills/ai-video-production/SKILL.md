---
name: ai-video-production
description: Production-grade programmatic AI video pipeline orchestration using local open-source TTS engines (Kokoro-82M, ChatTTS, F5-TTS, GPT-SoVITS, Edge-TTS), Alibaba SenseVoice millisecond alignment, and Remotion multi-core React video rendering.
---

# AI Video Studio: Programmatic Video Production Skill

## Overview
`ai-video-production` provides end-to-end guidance and scripts for producing high-fidelity, code-as-video technical explainers, tutorials, and social media shorts.

### Core Philosophy: Sound-First Determinism
1. **Audio as the Absolute Clock**: Video frames never dictate audio; rather, the physical millisecond duration of speech acts as the root time standard for all visual animations.
2. **State-Driven Visuals**: Every scene, subtitle bounce, and card transition is a pure deterministic function of `(frame, fps, timeline)`.
3. **Local-First Resilient TTS**: Zero-cloud dependency by deploying lightweight local models on CPU (Kokoro-82M, ChatTTS, F5-TTS, GPT-SoVITS) with automatic commercial neural voice fallbacks.

---

## 1. Local Open-Source TTS Engine Matrix

| Engine | Characteristics | Best Use Cases | Typical RTF / Speed |
|---|---|---|---|
| **Kokoro-82M** | 82M ONNX dynamic model, 103 Chinese & multilingual voice styles | Technical explainer, long tutorials, fast iteration | **0.05 RTF** (<2s per 50 chars on CPU) |
| **ChatTTS** | Conversational conversational flow, natural pauses, laughter & oral markers | Casual podcast, tech chat, geek commentary | **0.5~0.8 RTF** (~15s per 50 chars on CPU) |
| **F5-TTS** | Zero-shot flow-matching diffusion DiT acoustic model | Cinematic voiceover, deep narrator, diffusion showcase | **1.2~1.8 RTF** (~28s per 50 chars on CPU) |
| **GPT-SoVITS** | Few-shot fine-tuned voice cloning (5s to 1min voice clone) | Creator digital twin, character voice cloning | **0.6~1.0 RTF** via local HTTP API |
| **Edge-TTS** | Microsoft Azure cloud neural voices (`Yunxi`, `Xiaoxiao`, etc.) | High-availability fallback & reference benchmark | **Instant stream** |

---

## 2. Standard Data Contracts

### 2.1 Scene Script Contract (`content/scripts/*.json`)
```json
{
  "project": "07_transformer_case_study_kokoro",
  "engine": "kokoro",
  "voice": "zm_031",
  "fps": 30,
  "title": "Transformer 架构与注意力机制深度剖析",
  "scenes": [
    {
      "id": "scene_01",
      "title": "从循环神经网络到 Attention 的伟大飞跃",
      "badge": "HISTORICAL CONTEXT · 历史变革",
      "text": "分镜朗读中文文案...",
      "cards": [
        {
          "title": "RNN 串行瓶颈",
          "desc": "第 N 个时间步必须等待前 N-1 步计算完毕",
          "tag": "RNN BOTTLENECK",
          "icon": "⛓️"
        }
      ],
      "codeSnippet": "// optional code snippet",
      "codeLang": "rust"
    }
  ]
}
```

### 2.2 Timeline Contract (`public/timeline.json`)
Generated automatically by `scripts/sensevoice_aligner.py` using Alibaba SenseVoice-Small:
```json
{
  "project": "07_transformer_case_study_kokoro",
  "fps": 30,
  "totalDurationInFrames": 4754,
  "scenes": [
    {
      "id": "scene_01",
      "startFrame": 0,
      "durationInFrames": 543,
      "audioPath": "audio/scene_01.wav",
      "text": "文字内容...",
      "emotion": "<|NEUTRAL|>",
      "words": [
        {
          "text": "短语",
          "startFrame": 0,
          "endFrame": 54
        }
      ]
    }
  ]
}
```

---

## 3. Standard Pipeline Commands

### One-Click Execution Pipeline
```bash
# 1. End-to-end synthesize, align, validate and render
python scripts/pipeline.py --script content/scripts/07_transformer_flagship_case.json --project 07_transformer_case_study_kokoro --render --concurrency 4

# 2. Interactive preview in browser
npm run dev

# 3. Batch render all 10+ long videos
python scripts/batch_render_all.py
```

### Individual Step Commands
```bash
# Audio synthesis only
python scripts/generate_audio.py --script content/scripts/07_transformer_flagship_case.json

# Millisecond alignment & timeline contract generation
python scripts/sensevoice_aligner.py --script content/scripts/07_transformer_flagship_case.json --project my_project --fps 30

# Quality Gate inspection
python scripts/validator.py

# High-resolution rasterization
npx remotion render src/index.ts MasterVideo out/my_project.mp4 --concurrency=4
```

---

## 4. Quality Gate Checklist (Pre-Flight)
Before declaring any video completed or passing to rendering:
1. `timeline.json` exists, valid JSON, `totalDurationInFrames >= 3600` (at 30fps >= 120s).
2. All audio files in `public/audio/scene_*.{wav,mp3}` exist and have valid durations.
3. No cumulative drift between audio length and frame count (> 2 frames triggers failure).
4. All visual components (TerminalWindow, UniversalScene, DynamicSubtitles) resolve without React runtime errors.
