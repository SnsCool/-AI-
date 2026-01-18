# ナレッジベース API

FastAPIで構築されたバックエンドAPI。動画文字起こし、PDF OCR、ドキュメント管理を提供。

## セットアップ

```bash
cd api

# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
export GEMINI_API_KEY="your-api-key"
```

## 起動

```bash
# 開発モード（ホットリロード有効）
python run.py

# または直接uvicornで起動
uvicorn main:app --reload --port 8000
```

サーバーが起動したら:
- API: http://localhost:8000
- ドキュメント（Swagger UI）: http://localhost:8000/docs

## エンドポイント

### 文字起こし

| メソッド | パス | 説明 |
|----------|------|------|
| POST | `/api/transcribe/youtube` | YouTube動画の字幕を取得 |
| POST | `/api/transcribe/loom` | Loom動画の字幕を取得 |
| POST | `/api/transcribe/video` | 動画ファイルをGeminiで文字起こし |

### PDF OCR

| メソッド | パス | 説明 |
|----------|------|------|
| POST | `/api/ocr/pdf` | PDFをテキスト化（自動でOCR判定） |
| POST | `/api/ocr/pdf/force-ocr` | PDFを強制的にOCR処理 |

### ドキュメント

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/documents` | ドキュメント一覧を取得 |
| GET | `/api/documents/{id}` | ドキュメント詳細を取得 |

## 使用例

### YouTube文字起こし

```bash
curl -X POST "http://localhost:8000/api/transcribe/youtube" \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ"}'
```

### PDF OCR

```bash
curl -X POST "http://localhost:8000/api/ocr/pdf" \
  -F "file=@document.pdf"
```

### ドキュメント一覧

```bash
# すべて
curl "http://localhost:8000/api/documents"

# 文字起こしがあるもののみ
curl "http://localhost:8000/api/documents?filter=transcript"

# 検索
curl "http://localhost:8000/api/documents?search=会議"
```

## ターミナルから直接実行

APIを使わずに、既存のスクリプトを直接実行することも可能：

```bash
# YouTube文字起こし
python ../scripts/extract_youtube_transcripts.py

# 動画文字起こし（Gemini）
python ../scripts/transcribe_video_with_gemini.py video.mp4

# PDF OCR
python ../scripts/ocr_pdf_with_gemini.py document.pdf
```
