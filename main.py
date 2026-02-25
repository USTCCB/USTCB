"""
main.py  —— USTCB 日报主入口
GitHub Actions 直接运行此文件
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

from runner import DailyRunner

if __name__ == "__main__":
    DailyRunner().run()
