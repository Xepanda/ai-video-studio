"""
技术专有名词与多音字发音规范化预处理器 (G2P 纠音字典)
专门解决 TTS (ChatTTS, Edge-TTS 等) 在中英混读、英文缩写与技术多音字上的发音缺陷。

设计原则：
1. 真实中英混排无空格支持：使用 ASCII lookaround (?<![a-zA-Z0-9]) 替代 Unicode \\b，完美支持 "在NAS上"、"部署Nginx" 等语境。
2. 保护自然英文发音：不人为拆碎自然英语单词 (如保留 Docker、React、Git、Whisper、Kubernetes 的原生纯正发音)，仅纠偏易连读/念错字母的技术缩写。
3. 严格契约隔离：仅在进入 TTS 配音前对 speech_text 执行发音增强，字幕与 timeline.json 100% 保持原稿保真。
"""

import re
from typing import Dict, List, Tuple

# 1. 大写严格匹配的缩写词 (避免与日常英文单词混淆，如 ARM vs arm 手臂, RAM vs ram 撞击)
CASE_SENSITIVE_ACRONYM_MAP: Dict[str, str] = {
    "ARM": "A-R-M",
    "RAM": "R-A-M",
    "NAS": "纳斯",
    "FOC": "F-O-C",
    "BLDC": "B-L-D-C",
    "GGUF": "G-G-U-F",
    "RoPE": "Rope",
    "SwiGLU": "Swi-GLU",
    "K8s": "K-8-s",
    "RPC": "R-P-C",
    "gRPC": "g-R-P-C",
    "QPS": "Q-P-S",
    "TPS": "T-P-S",
    "AVX2": "A-V-X 2",
    "FP16": "F-P 16",
    "BF16": "B-F 16",
    "INT8": "Int 8",
    "INT4": "Int 4",
    "API": "A-P-I",
    "SDK": "S-D-K",
    "CLI": "C-L-I",
    "GUI": "G-U-I",
    "URL": "U-R-L",
    "HTTP": "H-T-T-P",
    "HTTPS": "H-T-T-P-S",
    "DNS": "D-N-S",
    "CDN": "C-D-N",
    "SSL": "S-S-L",
    "TLS": "T-L-S",
    "JSON": "J-Son",
    "HTML": "H-T-M-L",
    "CSS": "C-S-S",
    "SVG": "S-V-G",
    "CPU": "C-P-U",
    "GPU": "G-P-U",
    "SSD": "S-S-D",
    "ASR": "A-S-R",
    "TTS": "T-T-S",
    "LLM": "L-L-M",
    "RTF": "R-T-F",
    "VAD": "V-A-D",
    "BGM": "B-G-M",
    "SFX": "S-F-X",
    "ESP32": "E-S-P 32",
    "RISC-V": "Risk-Five",
}

# 2. 支持大小写不敏感的专有技术名词 (如 Nginx/nginx/NGINX -> Engine X)
CASE_INSENSITIVE_MAP: Dict[str, str] = {
    "nginx": "Engine X",
    "swiglu": "Swi-GLU",
    "vllm": "v-L-L-M",
    "flashattention": "Flash Attention",
    "pytorch": "Pie-Torch",
    "postgres": "Post-gres",
    "postgresql": "Post-gres",
    "mysql": "My-S-Q-L",
    "kafka": "卡夫卡",
    "redis": "雷迪斯",
    "remotion": "Re-motion",
    "cloudflare": "Cloud-flare",
    "modelscope": "Model-Scope",
}

# 预编译单遍扫描 Regex 模式 (ASCII 边界断言，按长度逆序匹配最长项)
_CASE_SENSITIVE_KEYS = sorted(CASE_SENSITIVE_ACRONYM_MAP.keys(), key=len, reverse=True)
_CASE_INSENSITIVE_KEYS = sorted(CASE_INSENSITIVE_MAP.keys(), key=len, reverse=True)

# 编译大写敏感正则
_SENSITIVE_PATTERN = re.compile(
    rf"(?<![a-zA-Z0-9])({'|'.join(re.escape(k) for k in _CASE_SENSITIVE_KEYS)})(?![a-zA-Z0-9])"
)

# 编译大小写泛化正则
_INSENSITIVE_PATTERN = re.compile(
    rf"(?<![a-zA-Z0-9])({'|'.join(re.escape(k) for k in _CASE_INSENSITIVE_KEYS)})(?![a-zA-Z0-9])",
    re.IGNORECASE
)

# 3. 中文多音字精准上下文规则
TECH_POLYPHONE_RULES: List[Tuple[re.Pattern, str]] = [
    # “行”：代码行/几行/行业/每行/第N行 (支持中文数字与阿拉伯数字，避让“行为”)
    (re.compile(r"第([零一二两三四五六七八九十百千万\d]+)行"), r"第\1航"),
    (re.compile(r"((?:每|这|那|上|下|几|多)[零一二两三四五六七八九十\d]?)行(?!为)"), r"\1航"),
    (re.compile(r"(代码|单|跨)行(?!为)"), r"\1航"),
    (re.compile(r"行业"), "航业"),

    # “调”：调度/调用/回调 读 diào (钓)；调优/调节/微调 读 tiáo (条)
    (re.compile(r"调度"), "钓度"),
    (re.compile(r"调用"), "钓用"),
    (re.compile(r"回调"), "回钓"),
    (re.compile(r"调优"), "条优"),
    (re.compile(r"调节"), "条节"),
    (re.compile(r"微调"), "微条"),

    # “重”：重构/重启/重试/重定向/重载/重写 读 chóng (虫)
    (re.compile(r"重(构|启|试|复|写|载|定向|新)"), r"虫\1"),
]


def normalize_tech_pronunciation(text: str) -> str:
    """
    对技术文案执行发音归一化，将可能造成 TTS 读音生硬、字母连读、多音字读错的词汇转为易于发音的形式。
    返回仅供 TTS 发音使用的增强文本。
    """
    if not text or not isinstance(text, str):
        return text

    # 1. 大小写敏感缩写替换 (单遍 O(L) 扫描)
    def _replace_sensitive(m: re.Match) -> str:
        word = m.group(1)
        return CASE_SENSITIVE_ACRONYM_MAP.get(word, word)

    normalized = _SENSITIVE_PATTERN.sub(_replace_sensitive, text)

    # 2. 大小写不敏感专有名词替换 (单遍 O(L) 扫描)
    def _replace_insensitive(m: re.Match) -> str:
        word = m.group(1).lower()
        return CASE_INSENSITIVE_MAP.get(word, m.group(1))

    normalized = _INSENSITIVE_PATTERN.sub(_replace_insensitive, normalized)

    # 3. 中文多音字上下文替换
    for pattern, replacement in TECH_POLYPHONE_RULES:
        normalized = pattern.sub(replacement, normalized)

    return normalized


if __name__ == "__main__":
    sample = (
        "在NAS上使用Docker部署NGINX与Redis，"
        "第一行代码就在优化SwiGLU和RoPE算子，"
        "系统调度器重启后，QPS和TPS提升了300%！"
    )
    print("原稿文本 (中英无空格):")
    print(sample)
    print("\n归一化发音文本:")
    print(normalize_tech_pronunciation(sample))
