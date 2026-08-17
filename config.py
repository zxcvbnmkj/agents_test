"""### 配置层（各框架共用）

集中管理模型连接信息，供各框架入口统一读取。

密钥只存放在仓库根目录的 `.env`（不入 git），本文件不出现任何密钥。

入口层引入方式：把仓库根目录 append 到 sys.path 后 `import config`。
用 append（而非 insert(0)）是为了不让根目录遮蔽 pydantic/langgraph 同名子目录。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# config.py 与 .env 同在仓库根目录
load_dotenv(Path(__file__).resolve().parent / '.env')

#: 模型名称（非密钥，可留默认）
MODEL_NAME = os.getenv('MODEL_NAME', 'doubao-seed-2.0-lite')

#: OpenAI 兼容网关地址（非密钥）
BASE_URL = os.getenv('OPENAI_BASE_URL')

#: API Key —— 仅从 .env 读取，缺失即报错，绝不内联
API_KEY = os.environ['OPENAI_API_KEY']
