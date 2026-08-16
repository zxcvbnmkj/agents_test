"""### 配置层

集中管理模型连接信息，供入口层（main.py）统一读取。

密钥只存放在仓库根目录的 `.env`（不入 git），本文件不出现任何密钥。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载仓库根目录的 .env（config.py 在 pydantic/ 下，根目录是其上一级）
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

#: 模型名称（非密钥，可留默认）
MODEL_NAME = os.getenv('MODEL_NAME', 'doubao-seed-2.0-lite')

#: OpenAI 兼容网关地址（非密钥）
BASE_URL = os.getenv('OPENAI_BASE_URL')

#: API Key —— 仅从 .env 读取，缺失即报错，绝不内联
API_KEY = os.environ['OPENAI_API_KEY']
