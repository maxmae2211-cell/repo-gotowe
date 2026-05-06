import unittest
import yaml
import json
from pathlib import Path


class TestConfigValidation(unittest.TestCase):
    def test_yaml_files(self):
        for yml in Path(".").glob("*.yml"):
            with self.subTest(yml=yml):
                with open(yml, encoding="utf-8") as f:
                    yaml.safe_load(f)

    def test_json_files(self):
        for js in Path(".").glob("*.json"):
            with self.subTest(js=js):
                with open(js, encoding="utf-8") as f:
                    json.load(f)


if __name__ == "__main__":
    unittest.main()
