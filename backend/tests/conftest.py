import os
import sys

# 让 `from app.xxx` 能从 backend 根目录解析
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 测试默认 token，确保需要鉴权的接口可被调用
os.environ.setdefault("FUND_AUTH_TOKEN", "test-token")
