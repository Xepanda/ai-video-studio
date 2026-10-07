"""
技术专有名词与多音字发音规范化预处理器 (G2P 纠音字典)
专门解决 TTS (ChatTTS, Edge-TTS 等) 在中英混读、英文缩写与技术多音字上的发音缺陷。

注意：
- 本模块仅在进入 TTS 配音合成前对输入文案进行发音调优替换。
- 视频字幕与时间轴契约 (timeline.json) 必须 100% 保持原始分镜文本，遵循“契约文字原稿保真原则”。
"""

import re
from typing import Dict, List, Tuple

# 1. 常见技术专有名词与英文缩写发音映射表 (单词边界匹配)
TECH_ACRONYM_MAP: Dict[str, str] = {
    # 架构与底层协议
    "Nginx": "Engine X",
    "nginx": "Engine X",
    "SwiGLU": "Swi-GLU",
    "swiglu": "Swi-GLU",
    "GGUF": "G-G-U-F",
    "gguf": "G-G-U-F",
    "FOC": "F-O-C",
    "foc": "F-O-C",
    "BLDC": "B-L-D-C",
    "bldc": "B-L-D-C",
    "NAS": "纳斯",
    "nas": "纳斯",
    "RoPE": "Rope",
    "rope": "Rope",
    "FlashAttention": "Flash Attention",
    "flashattention": "Flash Attention",
    "PyTorch": "Pie-Torch",
    "pytorch": "Pie-Torch",
    "vLLM": "v-L-L-M",
    "vllm": "v-L-L-M",
    "LLaMA": "拉马",
    "llama": "拉马",
    "Redis": "雷迪斯",
    "redis": "雷迪斯",
    "Docker": "Dock-er",
    "docker": "Dock-er",
    "Kubernetes": "K-8-s",
    "K8s": "K-8-s",
    "k8s": "K-8-s",
    "PostgreSQL": "Post-gres",
    "Postgres": "Post-gres",
    "MySQL": "My-S-Q-L",
    "mysql": "My-S-Q-L",
    "Kafka": "卡夫卡",
    "kafka": "卡夫卡",
    "RPC": "R-P-C",
    "rpc": "R-P-C",
    "gRPC": "g-R-P-C",
    "grpc": "g-R-P-C",
    "QPS": "Q-P-S",
    "qps": "Q-P-S",
    "TPS": "T-P-S",
    "tps": "T-P-S",
    "AVX2": "A-V-X 2",
    "avx2": "A-V-X 2",
    "CUDA": "酷达",
    "cuda": "酷达",
    "FP16": "F-P 16",
    "fp16": "F-P 16",
    "BF16": "B-F 16",
    "bf16": "B-F 16",
    "INT8": "Int 8",
    "int8": "Int 8",
    "INT4": "Int 4",
    "int4": "Int 4",
    "ONNX": "Onnx",
    "onnx": "Onnx",
    "Remotion": "Re-motion",
    "remotion": "Re-motion",
    "React": "瑞爱克特",
    "react": "瑞爱克特",
    "Git": "吉特",
    "git": "吉特",
    "GitHub": "Git-Hub",
    "github": "Git-Hub",
    "API": "A-P-I",
    "api": "A-P-I",
    "SDK": "S-D-K",
    "sdk": "S-D-K",
    "CLI": "C-L-I",
    "cli": "C-L-I",
    "GUI": "G-U-I",
    "gui": "G-U-I",
    "URL": "U-R-L",
    "url": "U-R-L",
    "HTTP": "H-T-T-P",
    "http": "H-T-T-P",
    "HTTPS": "H-T-T-P-S",
    "https": "H-T-T-P-S",
    "DNS": "D-N-S",
    "dns": "D-N-S",
    "CDN": "C-D-N",
    "cdn": "C-D-N",
    "SSL": "S-S-L",
    "ssl": "S-S-L",
    "TLS": "T-L-S",
    "tls": "T-L-S",
    "JSON": "J-Son",
    "json": "J-Son",
    "YAML": "雅么尔",
    "yaml": "雅么尔",
    "HTML": "H-T-M-L",
    "html": "H-T-M-L",
    "CSS": "C-S-S",
    "css": "C-S-S",
    "SVG": "S-V-G",
    "svg": "S-V-G",
    "CPU": "C-P-U",
    "cpu": "C-P-U",
    "GPU": "G-P-U",
    "gpu": "G-P-U",
    "RAM": "R-A-M",
    "ram": "R-A-M",
    "SSD": "S-S-D",
    "ssd": "S-S-D",
    "ASR": "A-S-R",
    "asr": "A-S-R",
    "TTS": "T-T-S",
    "tts": "T-T-S",
    "LLM": "L-L-M",
    "llm": "L-L-M",
    "RTF": "R-T-F",
    "rtf": "R-T-F",
    "VAD": "V-A-D",
    "vad": "V-A-D",
    "BGM": "B-G-M",
    "bgm": "B-G-M",
    "SFX": "S-F-X",
    "sfx": "S-F-X",
    "ESP32": "E-S-P 32",
    "esp32": "E-S-P 32",
    "ARM": "A-R-M",
    "arm": "A-R-M",
    "RISC-V": "Risk-Five",
    "risc-v": "Risk-Five",
    "Cloudflare": "Cloud-flare",
    "cloudflare": "Cloud-flare",
    "ModelScope": "Model-Scope",
    "modelscope": "Model-Scope",
    "Whisper": "Whisp-er",
    "whisper": "Whisp-er",
    "Paraformer": "Para-former",
    "paraformer": "Para-former",
}

# 2. 中文语境下容易读错的多音字词语匹配规则 (使用精准上下文正则)
TECH_POLYPHONE_RULES: List[Tuple[re.Pattern, str]] = [
    # “行”：代码行/几行/行业/每行/每一行读 háng (航)
    (re.compile(r"(每[一两三四五六七八九十\d]?)行"), r"\1航"),
    (re.compile(r"(几|代码|多)行"), r"\1航"),
    (re.compile(r"第(\d+)行"), r"第\1航"),
    (re.compile(r"行业"), "航业"),
    (re.compile(r"跨行"), "跨航"),

    # “调”：调度/调用读 diào (吊)；调优/调节/微调读 tiáo (条)
    (re.compile(r"调度"), "钓度"),
    (re.compile(r"调用"), "钓用"),
    (re.compile(r"调优"), "条优"),
    (re.compile(r"微调"), "微条"),

    # “重”：重构/重启/重试读 chóng (虫)；重要/权重读 zhòng (众)
    (re.compile(r"重构"), "虫构"),
    (re.compile(r"重启"), "虫启"),
    (re.compile(r"重试"), "虫试"),
    (re.compile(r"重复"), "虫复"),
]


def normalize_tech_pronunciation(text: str) -> str:
    """
    对技术文案执行发音归一化，将可能造成 TTS 读音生硬、字母连读、多音字读错的词汇转为易于发音的形式。
    返回仅供 TTS 发音使用的增强文本。
    """
    if not text or not isinstance(text, str):
        return text

    normalized = text

    # 1. 替换技术专有名词与英文缩写 (精确单词边界)
    for term, pronunciation in TECH_ACRONYM_MAP.items():
        pattern = r"\b" + re.escape(term) + r"\b"
        normalized = re.sub(pattern, pronunciation, normalized)

    # 2. 替换中文多音字特定词组
    for pattern, replacement in TECH_POLYPHONE_RULES:
        normalized = pattern.sub(replacement, normalized)

    return normalized


if __name__ == "__main__":
    # 单元自测演示
    sample = (
        "今天在 NAS 上用 Docker 部署 Nginx 与 Redis，"
        "每行代码都在优化 SwiGLU 和 RoPE 算子，"
        "系统调度器重启后，QPS 和 TPS 提升了 300%！"
    )
    print("原稿文本 (字幕契约用):")
    print(sample)
    print("\n归一化发音文本 (TTS 配音用):")
    print(normalize_tech_pronunciation(sample))
