import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.tech_phonetic_dict import normalize_tech_pronunciation, TECH_ACRONYM_MAP


class TestTechPhoneticDict(unittest.TestCase):

    def test_acronym_replacement(self):
        # 英文缩写替换
        text = "利用 Nginx 代理和 Redis 缓存，结合 SwiGLU 算子优化"
        res = normalize_tech_pronunciation(text)
        self.assertIn("Engine X", res)
        self.assertIn("雷迪斯", res)
        self.assertIn("Swi-GLU", res)
        self.assertNotIn("Nginx", res)

    def test_word_boundary_safety(self):
        # 单词边界保护，避免误伤单词中间的子串
        # 例如 "banana" 不应触发 "nas" 匹配
        text = "banana has nothing to do with NAS storage"
        res = normalize_tech_pronunciation(text)
        self.assertIn("banana", res)
        self.assertIn("纳斯", res)

    def test_polyphone_replacement(self):
        # 多音字上下文替换
        text = "今天调度系统需要重构，每一行代码都要微调优化"
        res = normalize_tech_pronunciation(text)
        self.assertIn("钓度", res)
        self.assertIn("虫构", res)
        self.assertIn("航", res)
        self.assertIn("微条", res)

    def test_empty_and_none(self):
        self.assertEqual(normalize_tech_pronunciation(""), "")
        self.assertIsNone(normalize_tech_pronunciation(None))


if __name__ == "__main__":
    unittest.main()
