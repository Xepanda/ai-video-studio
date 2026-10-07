import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.tech_phonetic_dict import normalize_tech_pronunciation


class TestTechPhoneticDict(unittest.TestCase):

    def test_chinese_english_no_space(self):
        # 验证中英文无空格混排边界正常识别 (解决 \b 遇到中文失效问题)
        text = "在NAS上部署NGINX与Redis，优化SwiGLU和RoPE算子"
        res = normalize_tech_pronunciation(text)
        self.assertIn("在纳斯上", res)
        self.assertIn("Engine X", res)
        self.assertIn("雷迪斯", res)
        self.assertIn("Swi-GLU", res)
        self.assertIn("Rope", res)

    def test_case_sensitivity_and_collision(self):
        # 大写敏感缩写词不应误伤普通英文小写单词
        text_lower = "an arm and a leg"
        res_lower = normalize_tech_pronunciation(text_lower)
        self.assertEqual(res_lower, "an arm and a leg")

        text_upper = "ARM Cortex-M4 处理器与 16GB RAM 内存"
        res_upper = normalize_tech_pronunciation(text_upper)
        self.assertIn("A-R-M", res_upper)
        self.assertIn("R-A-M", res_upper)

    def test_case_insensitive_acronyms(self):
        # 支持大小写泛化的技术专有名词
        self.assertIn("Engine X", normalize_tech_pronunciation("使用nginx"))
        self.assertIn("Engine X", normalize_tech_pronunciation("使用Nginx"))
        self.assertIn("Engine X", normalize_tech_pronunciation("使用NGINX"))
        self.assertIn("雷迪斯", normalize_tech_pronunciation("REDIS集群"))

    def test_polyphone_chinese_numerals(self):
        # 中文数字序号行与常用指代
        self.assertIn("第1航", normalize_tech_pronunciation("第1行代码"))
        self.assertIn("第一航", normalize_tech_pronunciation("第一行代码"))
        self.assertIn("第二十航", normalize_tech_pronunciation("第二十行代码"))
        self.assertIn("这一航", normalize_tech_pronunciation("这一行命令"))
        self.assertIn("每一航", normalize_tech_pronunciation("每一行文本"))

    def test_polyphone_avoid_false_positives(self):
        # “每行为规范” 不应被误伤为 “每航为规范”
        text = "每行为规范都经过审查"
        res = normalize_tech_pronunciation(text)
        self.assertEqual(res, text)

    def test_polyphone_tech_verbs(self):
        # 调度/回调/调优/重构/重写
        text = "系统调度器触发回调，对模型进行微调与重构重定向"
        res = normalize_tech_pronunciation(text)
        self.assertIn("钓度", res)
        self.assertIn("回钓", res)
        self.assertIn("微条", res)
        self.assertIn("虫构", res)
        self.assertIn("虫定向", res)

    def test_empty_and_none(self):
        self.assertEqual(normalize_tech_pronunciation(""), "")
        self.assertIsNone(normalize_tech_pronunciation(None))


if __name__ == "__main__":
    unittest.main()
