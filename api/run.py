#!/usr/bin/env python3
"""
APIサーバー起動スクリプト
"""

import os
import sys

# 環境変数の読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    import uvicorn

    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    reload = os.environ.get("API_RELOAD", "true").lower() == "true"

    print(f"🚀 APIサーバーを起動します: http://{host}:{port}")
    print(f"📚 ドキュメント: http://{host}:{port}/docs")
    print()

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
