import csv
from collections import Counter
from pathlib import Path

from lib.korean_dict.data_parser.BaseParser import BaseParser


class NameListParser(BaseParser):
    def parse(self, path_or_data: Path) -> Counter:
        ctr = Counter()
        with path_or_data.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                weight = row.get("weight", "").strip()
                if not name:
                    continue
                try:
                    w = int(weight)
                except ValueError:
                    continue
                ctr[name] += 1000000
        return ctr