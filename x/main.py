#!/usr/bin/env python3
"""
X Trend Video Fetcher & Mimic Post Generator

統合ワークフロー対応版

This script:
1. Fetches trending video tweets from X using Apify
2. Saves raw data to analysis/video_trends/ folder
3. Downloads videos in highest quality
4. Loads format templates from format/ folder
5. Uses brain data for style reference
6. Generates mimicking post text using Google Gemini
7. Uploads results to Google Drive
8. Posts to X (optional)

Workflow Integration:
- データ収集 → analysis/video_trends/ に保存
- フォーマット選択 → format/ から読み込み
- スタイル参照 → brain/ から読み込み
- 投稿作成 → Gemini で生成
- 投稿完了 → X に投稿
"""

import os
import json
import re
import sys
import tempfile
import glob as glob_module
from datetime import datetime
from pathlib import Path

import requests
import tweepy
from dotenv import load_dotenv
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration Constants (Edit these as needed)
# =============================================================================

# Target X accounts to fetch tweets from (multiple accounts supported)
TARGET_X_USERNAMES = [
    "masahirochaen",
    "Google",
]

# Number of tweets to fetch per account
MAX_TWEETS_PER_ACCOUNT = 1

# Total maximum tweets to process (for the workflow)
MAX_TWEETS = 10

# Maximum posts per day (business rule: 1日5投稿まで)
MAX_POSTS_PER_DAY = 5

# Gemini model to use
GEMINI_MODEL = "gemini-2.5-pro"

# =============================================================================
# Workflow Integration Paths
# =============================================================================

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Folder paths for workflow integration
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
VIDEO_TRENDS_DIR = ANALYSIS_DIR / "video_trends"
FORMAT_DIR = PROJECT_ROOT / "format"
BRAIN_DIR = PROJECT_ROOT / "brain"
INPUT_DIR = PROJECT_ROOT / "input"

# Default format template for video posts
DEFAULT_FORMAT = "05format-AI最新情報.md"

# System prompt for text generation
SYSTEM_PROMPT = """あなたはプロのSNSマーケターです。渡されたツイートの内容を要約・整理して、読みやすい投稿文を作成してください。

重要なポイント:
- 元ツイートの内容・事実・情報を忠実に保つこと（勝手に情報を追加・変更しない）
- 要約して読みやすく整理すること
- 絵文字は控えめに使用すること
- URLやリンクは一切含めないこと
- 「詳細はこちら」等のリンク誘導文は含めないこと（システムが自動追加します）
- 架空のURL、架空の情報、存在しない発表などを捏造しないこと"""

# =============================================================================
# Environment Variables (strip whitespace to avoid header errors)
# =============================================================================

def get_env(name: str) -> str | None:
    """Get environment variable and strip any whitespace."""
    value = os.getenv(name)
    if not value:
        return None
    # Strip whitespace
    value = value.strip()
    # For API tokens, remove any non-ASCII or control characters
    if name == "GEMINI_API_KEY":
        # Only keep alphanumeric, underscore, and hyphen
        value = re.sub(r'[^a-zA-Z0-9_\-]', '', value)
    return value

GEMINI_API_KEY = get_env("GEMINI_API_KEY")
GOOGLE_DRIVE_FOLDER_ID = get_env("GOOGLE_DRIVE_FOLDER_ID")
GCP_SA_KEY_JSON = get_env("GCP_SA_KEY_JSON")

# X (Twitter) API credentials
X_API_KEY = get_env("X_API_KEY")
X_API_SECRET = get_env("X_API_SECRET")
X_ACCESS_TOKEN = get_env("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = get_env("X_ACCESS_TOKEN_SECRET")
X_BEARER_TOKEN = get_env("X_BEARER_TOKEN")  # Required for fetching other users' tweets

# Enable/disable X posting (set to True to actually post)
ENABLE_X_POSTING = os.getenv("ENABLE_X_POSTING", "false").lower() == "true"

# Google Spreadsheet ID for logging (optional)
SPREADSHEET_ID = get_env("SPREADSHEET_ID")


def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "GOOGLE_DRIVE_FOLDER_ID": GOOGLE_DRIVE_FOLDER_ID,
        "GCP_SA_KEY_JSON": GCP_SA_KEY_JSON,
        "X_API_KEY": X_API_KEY,
        "X_API_SECRET": X_API_SECRET,
        "X_ACCESS_TOKEN": X_ACCESS_TOKEN,
        "X_ACCESS_TOKEN_SECRET": X_ACCESS_TOKEN_SECRET,
        "X_BEARER_TOKEN": X_BEARER_TOKEN,
    }

    missing = [name for name, value in required_vars.items() if not value]

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    print("✓ All environment variables validated", flush=True)


# =============================================================================
# X API: Tweet Fetching
# =============================================================================

def fetch_tweets_from_accounts(usernames: list[str], max_per_account: int = 3) -> list[dict]:
    """
    Fetch tweets from multiple accounts using X API (tweepy).

    Args:
        usernames: List of Twitter usernames to fetch from
        max_per_account: Maximum number of tweets per account

    Returns:
        List of tweet data dictionaries
    """
    print(f"Fetching tweets from {len(usernames)} accounts using X API...")
    print(f"  Accounts: {', '.join(['@' + u for u in usernames])}")

    # Check if X API credentials are available (Bearer Token required for fetching)
    if not X_BEARER_TOKEN:
        print("  X_BEARER_TOKEN not available - required for fetching other users' tweets")
        return []

    all_tweets = []

    try:
        # Create tweepy client with Bearer Token (required for fetching other users' tweets)
        client = tweepy.Client(bearer_token=X_BEARER_TOKEN)

        import time as time_module

        for idx, username in enumerate(usernames):
            print(f"\n  Fetching from @{username}...")

            # Add delay between accounts to avoid rate limiting (except first)
            if idx > 0:
                print(f"    Waiting 2 seconds to avoid rate limit...")
                time_module.sleep(2)

            try:
                # Get user ID from username
                user = client.get_user(username=username)
                if not user.data:
                    print(f"    User @{username} not found")
                    continue

                user_id = user.data.id
                print(f"    Found user ID: {user_id}")

                # Fetch user's tweets (exclude replies and retweets for better content)
                # Include note_tweet for long tweets (X Premium/Blue)
                tweets_response = client.get_users_tweets(
                    id=user_id,
                    max_results=max(5, min(max_per_account * 3, 100)),  # Fetch more to filter
                    tweet_fields=["created_at", "public_metrics", "attachments", "note_tweet"],
                    expansions=["attachments.media_keys", "author_id"],
                    media_fields=["type", "url", "preview_image_url", "variants"],
                    user_fields=["username", "name"],
                    exclude=["replies", "retweets"]  # Exclude replies and retweets
                )

                if not tweets_response.data:
                    print(f"    No tweets found for @{username}")
                    continue

                # Build media lookup dict
                media_dict = {}
                if tweets_response.includes and "media" in tweets_response.includes:
                    for media in tweets_response.includes["media"]:
                        media_dict[media.media_key] = media

                # Process tweets (limit to max_per_account, skip replies starting with @)
                tweets_to_process = []
                for tweet in tweets_response.data:
                    # Skip tweets that start with @ (replies/mentions)
                    if tweet.text.startswith("@"):
                        continue
                    tweets_to_process.append(tweet)
                    if len(tweets_to_process) >= max_per_account:
                        break

                for tweet in tweets_to_process:
                    # Use note_tweet for long tweets (X Premium), fall back to regular text
                    if hasattr(tweet, 'note_tweet') and tweet.note_tweet:
                        tweet_full_text = tweet.note_tweet.get('text', tweet.text)
                        print(f"      Long tweet detected: {len(tweet_full_text)} chars")
                    else:
                        tweet_full_text = tweet.text

                    tweet_dict = {
                        "id": tweet.id,
                        "id_str": str(tweet.id),
                        "text": tweet_full_text,
                        "full_text": tweet_full_text,
                        "created_at": str(tweet.created_at) if tweet.created_at else None,
                        "favorite_count": tweet.public_metrics.get("like_count", 0) if tweet.public_metrics else 0,
                        "retweet_count": tweet.public_metrics.get("retweet_count", 0) if tweet.public_metrics else 0,
                        "user": {
                            "screen_name": username,
                        }
                    }

                    # Add media info if available
                    if tweet.attachments and "media_keys" in tweet.attachments:
                        media_list = []
                        for media_key in tweet.attachments["media_keys"]:
                            if media_key in media_dict:
                                media = media_dict[media_key]
                                media_info = {
                                    "type": media.type,
                                    "url": getattr(media, "url", None),
                                    "preview_image_url": getattr(media, "preview_image_url", None),
                                }
                                if hasattr(media, "variants") and media.variants:
                                    media_info["video_info"] = {"variants": media.variants}
                                media_list.append(media_info)

                        if media_list:
                            tweet_dict["media"] = media_list
                            tweet_dict["extended_entities"] = {"media": media_list}

                    all_tweets.append(tweet_dict)

                print(f"    ✓ Using {len(tweets_to_process)} tweet(s)")

            except tweepy.errors.Forbidden as e:
                print(f"    X API access denied for @{username}: {e}")
                continue
            except tweepy.errors.Unauthorized as e:
                print(f"    X API unauthorized for @{username}: {e}")
                continue
            except Exception as e:
                print(f"    Error fetching @{username}: {e}")
                continue

        print(f"\n  ✓ Total fetched: {len(all_tweets)} tweets from {len(usernames)} accounts")

    except Exception as e:
        print(f"  X API error: {e}")
        return []

    # Debug: Print first tweet structure
    if all_tweets:
        print(f"\n========== DEBUG: FIRST TWEET STRUCTURE ==========", flush=True)
        print(f"Keys: {list(all_tweets[0].keys())}", flush=True)
        first_tweet_json = json.dumps(all_tweets[0], indent=2, default=str)
        if len(first_tweet_json) > 2000:
            first_tweet_json = first_tweet_json[:2000] + "\n... (truncated)"
        print(first_tweet_json, flush=True)
        print(f"========== END DEBUG ==========\n", flush=True)

    return all_tweets


# =============================================================================
# Workflow Integration: Analysis Folder
# =============================================================================

def save_tweets_to_analysis(tweets: list[dict], source: str = "video_trends") -> str:
    """
    Save fetched tweets to analysis folder for later use.

    Args:
        tweets: List of tweet data dictionaries
        source: Source identifier for the file name

    Returns:
        Path to saved file
    """
    # Ensure video_trends directory exists
    VIDEO_TRENDS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    accounts_str = "_".join(TARGET_X_USERNAMES[:3])  # First 3 accounts for filename
    file_name = f"{source}_{accounts_str}_{today}.json"
    file_path = VIDEO_TRENDS_DIR / file_name

    # Save as JSON for later processing
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": source,
            "target_accounts": TARGET_X_USERNAMES,
            "fetch_date": datetime.now().isoformat(),
            "tweet_count": len(tweets),
            "tweets": tweets
        }, f, ensure_ascii=False, indent=2, default=str)

    print(f"✓ Saved tweets to: {file_path}")

    # Also save a human-readable summary
    summary_file = VIDEO_TRENDS_DIR / f"{source}_{accounts_str}_{today}_summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"# Video Trend Analysis\n")
        f.write(f"# Accounts: {', '.join(['@' + u for u in TARGET_X_USERNAMES])}\n")
        f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Tweet Count: {len(tweets)}\n\n")

        for i, tweet in enumerate(tweets):
            tweet_id = tweet.get("id_str") or tweet.get("id") or str(i)
            full_text = tweet.get("full_text") or tweet.get("text", "")
            likes = tweet.get("favorite_count") or tweet.get("likeCount", 0)
            retweets = tweet.get("retweet_count") or tweet.get("retweetCount", 0)
            username = tweet.get("user", {}).get("screen_name", "unknown")

            f.write(f"--- Tweet {i + 1} (ID: {tweet_id}) @{username} ---\n")
            f.write(f"Likes: {likes} | Retweets: {retweets}\n")
            f.write(f"{full_text}\n\n")

    print(f"✓ Saved summary to: {summary_file}")

    return str(file_path)


def load_tweets_from_analysis(date_str: str = None) -> list[dict] | None:
    """
    Load previously saved tweets from analysis folder.

    Args:
        date_str: Date string in YYYYMMDD format (defaults to today)

    Returns:
        List of tweet data dictionaries or None if not found
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    pattern = str(VIDEO_TRENDS_DIR / f"*_{date_str}.json")
    files = glob_module.glob(pattern)

    if not files:
        print(f"No saved tweets found for {date_str}")
        return None

    # Use the most recent file
    file_path = sorted(files)[-1]
    print(f"Loading tweets from: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("tweets", [])


# =============================================================================
# Workflow Integration: Format Templates
# =============================================================================

def list_available_formats() -> list[str]:
    """
    List all available format templates.

    Returns:
        List of format file names
    """
    if not FORMAT_DIR.exists():
        print(f"Format directory not found: {FORMAT_DIR}")
        return []

    formats = sorted([f.name for f in FORMAT_DIR.glob("*.md")])
    return formats


def load_format_template(format_name: str = None) -> dict:
    """
    Load a format template from the format folder.

    Args:
        format_name: Name of the format file (defaults to DEFAULT_FORMAT)

    Returns:
        Dictionary with format content and metadata
    """
    if format_name is None:
        format_name = DEFAULT_FORMAT

    format_path = FORMAT_DIR / format_name

    if not format_path.exists():
        print(f"Format not found: {format_path}")
        print(f"Available formats: {list_available_formats()}")
        return {"name": format_name, "content": "", "found": False}

    with open(format_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"✓ Loaded format template: {format_name}")

    return {
        "name": format_name,
        "content": content,
        "found": True
    }


# =============================================================================
# Workflow Integration: Brain Data
# =============================================================================

def load_brain_data() -> str:
    """
    Load brain data for style reference.

    Returns:
        Combined brain data content as string
    """
    if not BRAIN_DIR.exists():
        print(f"Brain directory not found: {BRAIN_DIR}")
        return ""

    brain_files = list(BRAIN_DIR.glob("*.md"))

    if not brain_files:
        print("No brain data files found")
        return ""

    # Combine all brain data
    brain_content = []
    for file_path in sorted(brain_files):
        with open(file_path, "r", encoding="utf-8") as f:
            brain_content.append(f"# {file_path.name}\n\n{f.read()}")

    combined = "\n\n---\n\n".join(brain_content)
    print(f"✓ Loaded {len(brain_files)} brain data file(s)")

    return combined


def extract_video_url(tweet: dict) -> str | None:
    """
    Extract the highest quality video URL from a tweet.

    Args:
        tweet: Tweet data dictionary

    Returns:
        URL of the highest bitrate MP4 video, or None if not found
    """
    # Try multiple possible locations for media data
    media_list = []

    # Option 1: extendedEntities.media
    if tweet.get("extendedEntities", {}).get("media"):
        media_list = tweet["extendedEntities"]["media"]
        print(f"    Found media in extendedEntities", flush=True)

    # Option 2: extended_entities.media (snake_case)
    elif tweet.get("extended_entities", {}).get("media"):
        media_list = tweet["extended_entities"]["media"]
        print(f"    Found media in extended_entities", flush=True)

    # Option 3: entities.media
    elif tweet.get("entities", {}).get("media"):
        media_list = tweet["entities"]["media"]
        print(f"    Found media in entities", flush=True)

    # Option 4: Direct media array
    elif tweet.get("media"):
        media_list = tweet["media"] if isinstance(tweet["media"], list) else [tweet["media"]]
        print(f"    Found media in root", flush=True)

    # Option 5: Check for video directly
    elif tweet.get("video"):
        print(f"    Found video field directly", flush=True)
        video = tweet["video"]
        if isinstance(video, dict) and video.get("variants"):
            mp4_variants = [v for v in video["variants"] if v.get("content_type") == "video/mp4"]
            if mp4_variants:
                best = max(mp4_variants, key=lambda v: v.get("bitrate", 0))
                return best.get("url")

    if not media_list:
        print(f"    No media found in tweet", flush=True)

    for media in media_list:
        if media.get("type") == "video" or media.get("type") == "animated_gif":
            video_info = media.get("video_info", {})
            variants = video_info.get("variants", [])

            # Filter for MP4 variants and sort by bitrate
            mp4_variants = [
                v for v in variants
                if v.get("content_type") == "video/mp4" and v.get("bitrate") is not None
            ]

            if mp4_variants:
                # Select highest bitrate
                best_variant = max(mp4_variants, key=lambda v: v.get("bitrate", 0))
                return best_variant.get("url")

    return None


def download_video(url: str, tweet_id: str, output_dir: str) -> str | None:
    """
    Download a video from URL to local file.

    Args:
        url: Video URL
        tweet_id: Tweet ID for filename
        output_dir: Directory to save the video

    Returns:
        Path to downloaded file, or None if failed
    """
    try:
        print(f"  Downloading video for tweet {tweet_id}...")

        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        file_path = os.path.join(output_dir, f"tweet_{tweet_id}.mp4")

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(file_path)
        print(f"  ✓ Downloaded: {file_path} ({file_size / 1024 / 1024:.2f} MB)")
        return file_path

    except Exception as e:
        print(f"  ✗ Failed to download video: {e}")
        return None


# =============================================================================
# Google Gemini: Text Generation
# =============================================================================

def generate_mimic_text(
    original_text: str,
    format_template: dict = None,
    brain_data: str = None
) -> str:
    """
    Generate a mimicking post text using Google Gemini.

    Workflow Integration:
    - Uses format template for structure guidance
    - Uses brain data for style consistency

    Args:
        original_text: Original tweet text to mimic
        format_template: Format template dict from load_format_template()
        brain_data: Brain data string from load_brain_data()

    Returns:
        Generated mimicking text
    """
    # Configure Gemini
    genai.configure(api_key=GEMINI_API_KEY)

    # Build enhanced system prompt with brain data
    enhanced_system_prompt = SYSTEM_PROMPT

    if brain_data:
        enhanced_system_prompt += f"""

## 投稿スタイルガイドライン（Brain Data）:
{brain_data[:2000]}  # Limit to prevent too long prompts
"""

    # Create the model
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=enhanced_system_prompt
    )

    # Build user prompt with format template
    user_prompt = f"""以下のツイートの内容を要約・整理して、投稿文を作成してください。

元のツイート:
---
{original_text}
---
"""

    if format_template and format_template.get("found"):
        user_prompt += f"""
参考フォーマット（{format_template.get('name', 'default')}）:
---
{format_template.get('content', '')[:1500]}  # Limit format content
---
"""

    user_prompt += """
【重要な指示】
- 元ツイートの内容を忠実に要約すること（新しい情報を追加しない）
- URLは一切含めないこと
- 「詳細はこちら」などのリンク誘導文は含めないこと
- 200文字以内で作成し、投稿文のみを出力すること"""

    response = model.generate_content(user_prompt)

    return response.text


def save_generated_text(text: str, tweet_id: str, output_dir: str) -> str:
    """
    Save generated text to a file.

    Args:
        text: Generated text content
        tweet_id: Tweet ID for filename
        output_dir: Directory to save the file

    Returns:
        Path to saved file
    """
    file_path = os.path.join(output_dir, f"tweet_{tweet_id}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"  ✓ Saved generated text: {file_path}")
    return file_path


# =============================================================================
# Buzz Post Analysis & Template Generation
# =============================================================================

def load_buzz_posts() -> list[dict]:
    """
    Load buzz posts from JSON file.

    Returns:
        List of buzz post dictionaries
    """
    # PROJECT_ROOT is already the x/ directory
    buzz_file = os.path.join(PROJECT_ROOT, "buzz_posts.json")

    if not os.path.exists(buzz_file):
        print(f"  ✗ Buzz posts file not found: {buzz_file}")
        return []

    with open(buzz_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("buzz_posts", [])


def get_random_buzz_post() -> dict | None:
    """
    Get a random buzz post from the collection.

    Returns:
        Random buzz post dict or None if no posts available
    """
    import random
    buzz_posts = load_buzz_posts()

    if not buzz_posts:
        return None

    return random.choice(buzz_posts)


def analyze_buzz_post(buzz_content: str) -> dict:
    """
    Analyze a buzz post using 4-step prompt to extract structure and generate template.

    Args:
        buzz_content: The buzz post text to analyze

    Returns:
        Dictionary containing analysis results and generated prompt template
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=GEMINI_MODEL)

    analysis_prompt = f"""下記のステップに従って実行せよ

ステップ1: Xのポストの構成を割り出す
<<入力されたXのポストを一文ごとに分析し、構成要素を抽出する>>
制約条件
* 「。」を起点に文分ける
* 構成要素は10個以上出す（サボらないこと）
出力形式
* 構成1:
* 構成2:
* 構成3: ・・・
* 構成9: ・・・
* 構成N:

ステップ2: Xのポストの特徴を割り出す
<<Xのポストの特徴を分析し、以下の観点から特徴をリストアップする>>
* ジャンル:
* 文章の語調や口調:
* 使用されている説得テクニック:
* 訴求ポイント:
* 文章の構成パターン:
出力形式
* ジャンル:
* 文章の語調や口調:
* 使用されている説得テクニック:
* 訴求ポイント:
* 文章の構成パターン:

ステップ3: 構成と特徴を一般化する
<<ステップ1と2で割り出した構成・特徴を一般化し、汎用的な構成要素と制約条件を作成する>>
制約条件
* 構成要素は10個以上
出力形式
* 構成1:
* 構成2:
* 構成3: ・・・
* 構成9: ・・・
* 構成N:

ステップ4: プロンプトを作成する
<<ステップ3で一般化した構成と特徴を元に、汎用的なプロンプトを作成し、コードブロックで出力する>>

```
下記の命令を実行しXのポストを作成してください

### 命令書
あなたはプロのライターです。
no talk; just do
特徴を把握し、制約条件と構成に沿って「<<Xのポストのジャンル>>」のXのポストを出力してください。
「<<Xのポストの主題>>」はUSERに求めること
必ず回答例を参考にして、出力形式のような表で文章を出力してください。

### 制約条件:
<<ステップ2で割り出した特徴から、文章の制約条件としてそのまま記載>>

### ポスト特徴:
<<ステップ2で割り出した特徴から、Xのポストの特徴を記載>>

### 構成:
<<ステップ1で割り出した構成要素を一般化して列挙>>

### 回答例：
<<提出したXのポスト>>を<<一般化した構成>>に当てはめ、表形式として回答例にする
|一般化構成|提出Xのポスト|
|---|---|

### 出力形式
- 主題
---
|構成|文章|
|---|---|

```

---
入力されたXのポスト:
{buzz_content}
---

上記のステップ1〜4を実行し、結果を出力してください。"""

    print("  Analyzing buzz post structure...")
    response = model.generate_content(analysis_prompt)
    analysis_result = response.text

    # Extract the generated prompt from Step 4 (between ``` markers)
    import re
    prompt_match = re.search(r'```\n?(.*?)\n?```', analysis_result, re.DOTALL)
    generated_prompt = prompt_match.group(1) if prompt_match else None

    return {
        "buzz_content": buzz_content,
        "analysis": analysis_result,
        "generated_prompt": generated_prompt
    }


def generate_post_with_template(
    analysis_result: dict,
    source_tweet: str,
    source_username: str = ""
) -> str:
    """
    Generate a new post using the prompt generated from Step 4.

    Args:
        analysis_result: Result from analyze_buzz_post() containing generated_prompt
        source_tweet: The fetched tweet content to use as 主題 (subject)
        source_username: Username of the source tweet author

    Returns:
        Generated post text
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=GEMINI_MODEL)

    generated_prompt = analysis_result.get("generated_prompt", "")

    if not generated_prompt:
        # Fallback if no generated prompt available
        print("  ⚠ No generated prompt from Step 4, using fallback")
        return None

    # Use the generated prompt from Step 4, with source tweet as the 主題
    final_prompt = f"""{generated_prompt}

### 主題（この内容を元に投稿を作成）:
{source_tweet}

※追加制約: 200文字以内で作成すること（X Free アカウント対応）
※出力は投稿文のテキストのみ（表形式ではなく、テキストのみ出力）"""

    print("  Generating post with template...")
    response = model.generate_content(final_prompt)

    # Extract text content (remove table formatting if present)
    result_text = response.text.strip()

    # If result contains table format, extract the text content
    if "|" in result_text:
        lines = result_text.split("\n")
        text_parts = []
        for line in lines:
            if "|" in line and "---" not in line and "構成" not in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    text_parts.append(parts[2].strip())
        if text_parts:
            result_text = "".join(text_parts)

    return result_text


# =============================================================================
# Google Spreadsheet: Logging
# =============================================================================

def get_sheets_service():
    """
    Create and return a Google Sheets API service instance.

    Returns:
        Google Sheets API service instance
    """
    credentials_info = json.loads(GCP_SA_KEY_JSON)

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    return build("sheets", "v4", credentials=credentials)


def append_to_spreadsheet(
    sheet_id: str,
    row_data: dict
) -> bool:
    """
    Append a row to the spreadsheet for logging.

    Args:
        sheet_id: Google Spreadsheet ID
        row_data: Dictionary containing row data:
            - datetime: 投稿日時
            - status: 成功/失敗
            - source_account: 取得元アカウント
            - source_content: 取得ツイート内容
            - generated_content: 生成投稿内容
            - post_url: 投稿URL
            - source_url: ソースURL

    Returns:
        True if successful, False otherwise
    """
    try:
        service = get_sheets_service()

        # Prepare row values
        row = [
            row_data.get("datetime", ""),
            row_data.get("status", ""),
            row_data.get("source_account", ""),
            row_data.get("source_content", ""),
            row_data.get("generated_content", ""),
            row_data.get("post_url", ""),
            row_data.get("source_url", "")
        ]

        # Append to sheet
        body = {"values": [row]}

        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="投稿ログ!A:G",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"  ✓ Logged to spreadsheet")
        return True

    except Exception as e:
        print(f"  ✗ Failed to log to spreadsheet: {e}")
        return False


# =============================================================================
# Google Drive: Upload
# =============================================================================

def get_drive_service():
    """
    Create and return a Google Drive API service instance.

    Uses service account credentials from environment variable.

    Returns:
        Google Drive API service instance
    """
    # Parse JSON from environment variable
    credentials_info = json.loads(GCP_SA_KEY_JSON)

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )

    service = build("drive", "v3", credentials=credentials)
    return service


def get_or_create_date_folder(service, parent_folder_id: str, date_str: str) -> str:
    """
    Get or create a date-based subfolder in Google Drive.

    Args:
        service: Google Drive API service
        parent_folder_id: Parent folder ID
        date_str: Date string for folder name (e.g., "2025-05-20")

    Returns:
        Folder ID of the date folder
    """
    # Search for existing folder
    query = (
        f"'{parent_folder_id}' in parents and "
        f"name = '{date_str}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )

    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])

    if files:
        folder_id = files[0]["id"]
        print(f"  Using existing folder: {date_str}")
        return folder_id

    # Create new folder
    folder_metadata = {
        "name": date_str,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id]
    }

    folder = service.files().create(
        body=folder_metadata,
        fields="id"
    ).execute()

    folder_id = folder.get("id")
    print(f"  ✓ Created new folder: {date_str}")
    return folder_id


def upload_to_drive(service, file_path: str, folder_id: str) -> str:
    """
    Upload a file to Google Drive.

    Args:
        service: Google Drive API service
        file_path: Local file path
        folder_id: Destination folder ID

    Returns:
        Uploaded file ID
    """
    file_name = os.path.basename(file_path)

    # Determine MIME type
    if file_path.endswith(".mp4"):
        mime_type = "video/mp4"
    elif file_path.endswith(".txt"):
        mime_type = "text/plain"
    else:
        mime_type = "application/octet-stream"

    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name"
    ).execute()

    print(f"  ✓ Uploaded to Drive: {file_name}")
    return file.get("id")


# =============================================================================
# X (Twitter) API: Posting
# =============================================================================

def get_x_client() -> tuple[tweepy.Client, tweepy.API]:
    """
    Create and return X API client instances.

    Returns:
        Tuple of (tweepy.Client for v2 API, tweepy.API for v1.1 media upload)
    """
    # v2 Client for posting tweets
    client = tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET
    )

    # v1.1 API for media upload (required for video)
    auth = tweepy.OAuth1UserHandler(
        X_API_KEY,
        X_API_SECRET,
        X_ACCESS_TOKEN,
        X_ACCESS_TOKEN_SECRET
    )
    api = tweepy.API(auth)

    return client, api


def upload_video_to_x(api: tweepy.API, video_path: str) -> str | None:
    """
    Upload a video to X and return the media_id.

    Args:
        api: tweepy.API instance for v1.1 API
        video_path: Path to the video file

    Returns:
        media_id string or None if failed
    """
    try:
        print(f"  Uploading video to X...", flush=True)

        # Check file size (X limit is 512MB for video)
        file_size = os.path.getsize(video_path)
        print(f"    Video size: {file_size / 1024 / 1024:.2f} MB", flush=True)

        if file_size > 512 * 1024 * 1024:
            print(f"  ✗ Video too large (max 512MB)", flush=True)
            return None

        # Upload video using chunked upload
        media = api.media_upload(
            filename=video_path,
            media_category="tweet_video",
            chunked=True
        )

        print(f"  ✓ Video uploaded to X, media_id: {media.media_id_string}", flush=True)
        return media.media_id_string

    except Exception as e:
        print(f"  ✗ Failed to upload video to X: {e}", flush=True)
        return None


def post_to_x(client: tweepy.Client, text: str, media_id: str = None, source_url: str = None) -> str | None:
    """
    Post a tweet to X.

    Args:
        client: tweepy.Client instance for v2 API
        text: Tweet text
        media_id: Optional media_id for video attachment
        source_url: Optional source tweet URL to append at the end

    Returns:
        Tweet ID or None if failed
    """
    try:
        print(f"  Posting to X...", flush=True)

        # Remove hallucinated URLs and placeholder text from Gemini-generated text
        import re
        text = re.sub(r'https?://\S+', '', text)  # Remove actual URLs
        text = re.sub(r'\[.*?URL.*?\]', '', text)  # Remove placeholder like [〇〇URL]
        text = re.sub(r'詳細はこちら[:：]?\s*$', '', text)  # Remove orphaned "詳細はこちら"
        text = re.sub(r'\s+', ' ', text).strip()  # Clean up extra whitespace

        # Add source URL at the end if provided
        if source_url:
            source_suffix = f"\n\n詳細はこちら: {source_url}"
            # Calculate max length for main text (280 - source suffix length)
            max_main_text_len = 280 - len(source_suffix)
            if len(text) > max_main_text_len:
                text = text[:max_main_text_len - 3] + "..."
            text = text + source_suffix
            print(f"    Added source URL: {source_url}", flush=True)
        elif len(text) > 280:
            # Truncate text if too long (X limit is 280 characters)
            text = text[:277] + "..."
            print(f"    Text truncated to 280 chars", flush=True)

        # Post tweet
        if media_id:
            response = client.create_tweet(text=text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=text)

        tweet_id = response.data["id"]
        print(f"  ✓ Posted to X! Tweet ID: {tweet_id}", flush=True)
        print(f"    URL: https://x.com/i/status/{tweet_id}", flush=True)

        return tweet_id

    except Exception as e:
        print(f"  ✗ Failed to post to X: {e}", flush=True)
        return None


def test_x_posting():
    """Test X posting functionality with a simple test tweet."""
    print("=" * 60)
    print("X Posting Test")
    print("=" * 60)
    print()

    # Check X credentials
    x_vars = {
        "X_API_KEY": X_API_KEY,
        "X_API_SECRET": X_API_SECRET,
        "X_ACCESS_TOKEN": X_ACCESS_TOKEN,
        "X_ACCESS_TOKEN_SECRET": X_ACCESS_TOKEN_SECRET,
    }

    missing = [name for name, value in x_vars.items() if not value]
    if missing:
        print(f"✗ Missing X API credentials: {', '.join(missing)}")
        return False

    print("✓ X API credentials found")

    try:
        # Get clients
        client, api = get_x_client()

        # Verify credentials
        print("Verifying credentials...", flush=True)
        user = api.verify_credentials()
        print(f"✓ Authenticated as: @{user.screen_name}", flush=True)

        # Post test tweet (text only)
        test_text = f"🤖 X API テスト投稿 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nこれはテスト投稿です。自動的に削除されます。"

        print(f"\nPosting test tweet...", flush=True)
        response = client.create_tweet(text=test_text)
        tweet_id = response.data["id"]

        print(f"✓ Test tweet posted successfully!")
        print(f"  Tweet ID: {tweet_id}")
        print(f"  URL: https://x.com/i/status/{tweet_id}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


# =============================================================================
# Main Processing
# =============================================================================

def process_tweets(format_name: str = None, skip_x_post: bool = True, max_posts: int = MAX_POSTS_PER_DAY):
    """
    Main function to process tweets and upload results.

    Workflow Integration:
    1. データ収集 - Fetch tweets from X via Apify
    2. 分析・格納 - Save to analysis/video_trends/
    3. フォーマット選択 - Load format template
    4. スタイル参照 - Load brain data
    5. 投稿作成 - Generate text with Gemini
    6. 投稿完了 - Upload to Drive and optionally post to X

    Args:
        format_name: Optional format template name to use
        skip_x_post: Skip X posting (default True for safety)
        max_posts: Maximum posts per day (default: MAX_POSTS_PER_DAY)
    """
    print("=" * 60)
    print("X Trend Video Fetcher & Mimic Post Generator")
    print("統合ワークフロー版")
    print("=" * 60)
    print()
    print(f"Business Rules: Max {max_posts} posts/day, fetching from {len(TARGET_X_USERNAMES)} accounts")
    print()

    # Validate environment
    validate_environment()
    print()

    # ==========================================================================
    # Workflow Step 1: データ収集 (Data Collection)
    # ==========================================================================
    print("=" * 40)
    print("Step 1: データ収集 (Data Collection)")
    print("=" * 40)
    print(f"Target accounts: {len(TARGET_X_USERNAMES)} accounts")
    tweets = fetch_tweets_from_accounts(TARGET_X_USERNAMES, MAX_TWEETS_PER_ACCOUNT)
    print()

    if not tweets:
        print("No tweets found. Attempting fallback posting...")

        # Fallback: Generate and post an AI-related tweet using Gemini
        if not skip_x_post and ENABLE_X_POSTING:
            print("\n========================================")
            print("Fallback: Generating tweet with Gemini")
            print("========================================")

            try:
                # Generate unique fallback content using Gemini
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel(model_name=GEMINI_MODEL)

                fallback_prompt = """AI・テクノロジーに関する短いツイートを1つ生成してください。

条件:
- 200文字以内
- 日本語で
- AI、機械学習、テクノロジーの最新トレンドや考察について
- 絵文字は1〜2個程度
- URLは含めない
- 「詳細はこちら」などのリンク誘導文は含めない
- 毎回異なる内容になるようにユニークな視点で
- 投稿文のみを出力（説明や前置きは不要）"""

                print("  Generating with Gemini...")
                response = model.generate_content(fallback_prompt)
                fallback_text = response.text.strip()
                print(f"  Generated: {fallback_text[:50]}...")

                client, api = get_x_client()
                print(f"  Posting fallback tweet...")
                tweet_id = post_to_x(client, fallback_text)
                if tweet_id:
                    print(f"  ✓ Fallback tweet posted successfully!")
                else:
                    print(f"  ✗ Failed to post fallback tweet")
            except Exception as e:
                print(f"  ✗ Fallback posting failed: {e}")
        else:
            print("X posting disabled, skipping fallback.")

        return

    # ==========================================================================
    # Workflow Step 2: 分析・格納 (Analysis & Storage)
    # ==========================================================================
    print("=" * 40)
    print("Step 2: 分析・格納 (Analysis & Storage)")
    print("=" * 40)
    save_tweets_to_analysis(tweets, source="video_trends")
    print()

    # ==========================================================================
    # Workflow Step 3: フォーマット選択 (Format Selection)
    # ==========================================================================
    print("=" * 40)
    print("Step 3: フォーマット選択 (Format Selection)")
    print("=" * 40)
    print(f"Available formats: {list_available_formats()}")
    format_template = load_format_template(format_name)
    print()

    # ==========================================================================
    # Workflow Step 4: スタイル参照 (Style Reference)
    # ==========================================================================
    print("=" * 40)
    print("Step 4: スタイル参照 (Brain Data)")
    print("=" * 40)
    brain_data = load_brain_data()
    print()

    # ==========================================================================
    # Workflow Step 5: 投稿作成 (Post Creation) - バズ投稿テンプレート方式
    # ==========================================================================
    print("=" * 40)
    print("Step 5: 投稿作成 (Post Creation)")
    print("=" * 40)

    # Select random buzz post for template analysis
    print("Selecting random buzz post for template analysis...")
    buzz_post = get_random_buzz_post()
    if buzz_post:
        print(f"  ✓ Selected buzz post: {buzz_post.get('id', 'unknown')}")
        print(f"    Preview: {buzz_post.get('content', '')[:80]}...")

        # Analyze buzz post structure (4-step prompt)
        print("  Analyzing buzz post structure...")
        try:
            analysis_result = analyze_buzz_post(buzz_post.get("content", ""))
            print(f"  ✓ Analysis complete")
        except Exception as e:
            print(f"  ✗ Buzz post analysis failed: {e}")
            analysis_result = None
    else:
        print("  ⚠ No buzz posts available, using fallback generation")
        analysis_result = None

    # Initialize Google Drive
    print("\nInitializing Google Drive...")
    drive_service = get_drive_service()
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder_id = get_or_create_date_folder(
        drive_service,
        GOOGLE_DRIVE_FOLDER_ID,
        today
    )
    print()

    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        print()

        processed_count = 0
        generated_posts = []

        for i, tweet in enumerate(tweets):
            tweet_id = tweet.get("id_str") or tweet.get("id") or str(i)
            full_text = tweet.get("full_text") or tweet.get("text", "")
            source_username = tweet.get("user", {}).get("screen_name", "")

            # Extract content URL from original tweet (use the FIRST t.co URL)
            # The first URL is usually the main content (video/article), later URLs may be images
            all_urls = re.findall(r'https?://t\.co/\S+', full_text)
            content_url = all_urls[0] if all_urls else None  # Get the first URL

            print(f"\n[Tweet {i + 1}/{len(tweets)}] ID: {tweet_id}")
            if all_urls:
                print(f"  Found {len(all_urls)} URL(s), using first: {content_url}")
            print(f"  Text preview: {full_text[:100]}...")

            # Extract video URL (optional - text-only posts are now supported)
            video_url = extract_video_url(tweet)
            video_path = None

            if video_url:
                # Download video if available
                video_path = download_video(video_url, tweet_id, temp_dir)
                if not video_path:
                    print("  ⚠ Failed to download video, continuing with text-only...")
            else:
                print("  ℹ No video in this tweet, generating text-only post...")

            # Generate post using buzz post template or fallback
            print("  Generating post with Gemini...")
            try:
                if analysis_result:
                    # Use buzz post template-based generation
                    print(f"    Using buzz post template: {buzz_post.get('id', 'unknown')}")
                    generated_text = generate_post_with_template(
                        analysis_result,
                        full_text,
                        source_username
                    )
                else:
                    # Fallback to original generation method
                    print(f"    Using format: {format_template.get('name', 'default')}")
                    print(f"    Using brain data: {'Yes' if brain_data else 'No'}")
                    generated_text = generate_mimic_text(
                        full_text,
                        format_template=format_template,
                        brain_data=brain_data
                    )
                text_path = save_generated_text(generated_text, tweet_id, temp_dir)
            except Exception as e:
                print(f"  ✗ Failed to generate text: {e}")
                continue

            # Upload to Google Drive
            print("  Uploading to Google Drive...")
            try:
                if video_path:
                    upload_to_drive(drive_service, video_path, date_folder_id)
                upload_to_drive(drive_service, text_path, date_folder_id)
                processed_count += 1

                # Store generated post info
                generated_posts.append({
                    "tweet_id": tweet_id,
                    "source_username": source_username,
                    "content_url": content_url,  # URL from original tweet (e.g., https://t.co/xxx)
                    "original_text": full_text,
                    "generated_text": generated_text,
                    "video_path": video_path  # Can be None for text-only posts
                })

            except Exception as e:
                print(f"  ✗ Failed to upload: {e}")
                continue

            # Stop if we've processed enough tweets
            if processed_count >= MAX_TWEETS:
                break

        # ======================================================================
        # Workflow Step 6: 投稿完了 (Post Completion)
        # ======================================================================
        print()
        print("=" * 40)
        print("Step 6: 投稿完了 (Post Completion)")
        print("=" * 40)

        if not skip_x_post and ENABLE_X_POSTING and generated_posts:
            # Apply max_posts limit
            posts_to_publish = generated_posts[:max_posts]
            print(f"X posting is enabled. Posting {len(posts_to_publish)} tweets to X (max: {max_posts})...")

            if len(generated_posts) > max_posts:
                print(f"  ⚠ Limiting from {len(generated_posts)} to {max_posts} posts (daily limit)")

            try:
                client, api = get_x_client()
                posted_count = 0

                # Post limited content
                for idx, post in enumerate(posts_to_publish):
                    print(f"\n  [{idx + 1}/{len(posts_to_publish)}] Posting tweet...")

                    try:
                        # Check if video exists
                        video_path = post.get("video_path")
                        media_id = None

                        # Use tweet URL (t.co URLs cause 403 Forbidden errors)
                        source_username = post.get("source_username", "")
                        source_tweet_id = post.get("tweet_id", "")

                        if source_username and source_tweet_id:
                            source_url = f"https://x.com/{source_username}/status/{source_tweet_id}"
                        else:
                            source_url = None

                        if video_path:
                            media_id = upload_video_to_x(api, video_path)

                        posted_tweet_id = None
                        post_status = "失敗"

                        if media_id:
                            posted_tweet_id = post_to_x(client, post["generated_text"], media_id, source_url)
                            if posted_tweet_id:
                                posted_count += 1
                                post_status = "成功"
                                print(f"    ✓ Posted with video!")
                        else:
                            # Post text only (no video or video upload failed)
                            if video_path:
                                print("    ⚠ Video upload failed, posting text only...")
                            else:
                                print("    ℹ Posting text only...")
                            posted_tweet_id = post_to_x(client, post["generated_text"], source_url=source_url)
                            if posted_tweet_id:
                                posted_count += 1
                                post_status = "成功"
                                print(f"    ✓ Posted successfully!")

                        # Log to spreadsheet if SPREADSHEET_ID is configured
                        if SPREADSHEET_ID:
                            post_url = f"https://x.com/i/status/{posted_tweet_id}" if posted_tweet_id else ""
                            log_data = {
                                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": post_status,
                                "source_account": f"@{source_username}" if source_username else "",
                                "source_content": post.get("original_text", "")[:500],  # Limit length
                                "generated_content": post.get("generated_text", "")[:500],  # Limit length
                                "post_url": post_url,
                                "source_url": source_url or ""
                            }
                            append_to_spreadsheet(SPREADSHEET_ID, log_data)

                    except Exception as e:
                        print(f"    ✗ Failed to post: {e}")
                        # Log failure to spreadsheet
                        if SPREADSHEET_ID:
                            log_data = {
                                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": "失敗",
                                "source_account": f"@{source_username}" if source_username else "",
                                "source_content": post.get("original_text", "")[:500],
                                "generated_content": post.get("generated_text", "")[:500],
                                "post_url": "",
                                "source_url": source_url or ""
                            }
                            append_to_spreadsheet(SPREADSHEET_ID, log_data)
                        continue

                    # Wait between posts to avoid rate limiting (except for last post)
                    if idx < len(posts_to_publish) - 1:
                        import time
                        print("    Waiting 30 seconds before next post...")
                        time.sleep(30)

                print(f"\n✓ Posted {posted_count}/{len(posts_to_publish)} tweets to X!")

            except Exception as e:
                print(f"✗ X posting failed: {e}")
        else:
            if skip_x_post:
                print("X posting skipped (skip_x_post=True)")
            elif not ENABLE_X_POSTING:
                print("X posting disabled (ENABLE_X_POSTING=false)")
            else:
                print("No posts generated to publish")

        # Save generated posts summary to analysis folder
        if generated_posts:
            summary_path = VIDEO_TRENDS_DIR / f"generated_posts_{datetime.now().strftime('%Y%m%d')}.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump({
                    "date": datetime.now().isoformat(),
                    "format_used": format_template.get("name", "default"),
                    "posts": [
                        {
                            "tweet_id": p["tweet_id"],
                            "original_text": p["original_text"],
                            "generated_text": p["generated_text"]
                        } for p in generated_posts
                    ]
                }, f, ensure_ascii=False, indent=2)
            print(f"✓ Saved generated posts summary: {summary_path}")

        print()
        print("=" * 60)
        print(f"Workflow complete! {processed_count} tweets processed.")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  - Tweets fetched: {len(tweets)}")
        print(f"  - Posts generated: {len(generated_posts)}")
        print(f"  - Format used: {format_template.get('name', 'default')}")
        print(f"  - Brain data: {'Loaded' if brain_data else 'Not found'}")
        print(f"  - X posting: {'Enabled' if ENABLE_X_POSTING and not skip_x_post else 'Disabled'}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="X Trend Video Fetcher & Mimic Post Generator (統合ワークフロー版)"
    )
    parser.add_argument(
        "--test-x",
        action="store_true",
        help="Test X posting functionality (posts a test tweet)"
    )
    parser.add_argument(
        "--test-x-video",
        type=str,
        metavar="VIDEO_PATH",
        help="Test X posting with a video file"
    )
    parser.add_argument(
        "--format",
        type=str,
        metavar="FORMAT_NAME",
        help="Format template to use (e.g., '05format-AI最新情報.md')"
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List all available format templates"
    )
    parser.add_argument(
        "--post-to-x",
        action="store_true",
        help="Enable posting to X (disabled by default)"
    )
    parser.add_argument(
        "--commander",
        action="store_true",
        help="Use Commander Agent to orchestrate tasks (AI-driven task routing)"
    )
    parser.add_argument(
        "--request",
        type=str,
        metavar="REQUEST",
        help="Request to send to Commander Agent (use with --commander)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=MAX_POSTS_PER_DAY,
        metavar="N",
        help=f"Maximum posts per day (default: {MAX_POSTS_PER_DAY})"
    )

    args = parser.parse_args()

    if args.commander:
        # Run Commander Agent orchestration mode
        print("=" * 60)
        print("Commander Agent Mode")
        print("=" * 60)
        print()

        # Get request from argument or use default
        request = args.request or "X投稿ワークフローを実行してください"
        print(f"Request: {request}")
        print()

        try:
            # Import and register agents
            from agents.registry import AgentRegistry
            from agents.commander.commander import CommanderAgent
            from agents.execution.x_posting import XPostingAgent

            # Register agents
            print("Registering agents...")
            AgentRegistry.register(CommanderAgent())
            AgentRegistry.register(XPostingAgent())
            print()

            # Get commander and orchestrate
            commander = AgentRegistry.get_commander()
            if not commander:
                print("✗ Commander agent not found")
                sys.exit(1)

            print(f"Starting orchestration with Commander Agent...")
            print()

            result = commander.orchestrate(request)

            print()
            print("=" * 60)
            print("Orchestration Result")
            print("=" * 60)
            print(f"Success: {result.success}")
            print(f"Message: {result.message}")
            if result.data:
                print(f"Data: {json.dumps(result.data, ensure_ascii=False, indent=2)}")
            if result.error:
                print(f"Error: {result.error}")

        except ImportError as e:
            print(f"✗ Failed to import agents: {e}")
            print("Make sure you're running from the x/ directory")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Commander failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elif args.list_formats:
        # List available formats
        print("Available format templates:")
        for fmt in list_available_formats():
            print(f"  - {fmt}")
        sys.exit(0)
    elif args.test_x:
        # Run X posting test (text only)
        test_x_posting()
    elif args.test_x_video:
        # Run X posting test with video
        print("=" * 60)
        print("X Video Posting Test")
        print("=" * 60)
        print()

        if not os.path.exists(args.test_x_video):
            print(f"✗ Video file not found: {args.test_x_video}")
            sys.exit(1)

        # Check X credentials
        x_vars = {
            "X_API_KEY": X_API_KEY,
            "X_API_SECRET": X_API_SECRET,
            "X_ACCESS_TOKEN": X_ACCESS_TOKEN,
            "X_ACCESS_TOKEN_SECRET": X_ACCESS_TOKEN_SECRET,
        }

        missing = [name for name, value in x_vars.items() if not value]
        if missing:
            print(f"✗ Missing X API credentials: {', '.join(missing)}")
            sys.exit(1)

        print("✓ X API credentials found")

        try:
            client, api = get_x_client()

            # Verify credentials
            print("Verifying credentials...", flush=True)
            user = api.verify_credentials()
            print(f"✓ Authenticated as: @{user.screen_name}", flush=True)

            # Upload video
            media_id = upload_video_to_x(api, args.test_x_video)
            if not media_id:
                print("✗ Failed to upload video")
                sys.exit(1)

            # Post tweet with video
            test_text = f"🎬 動画投稿テスト - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            tweet_id = post_to_x(client, test_text, media_id)

            if tweet_id:
                print(f"\n✓ Video tweet posted successfully!")
            else:
                print(f"\n✗ Failed to post video tweet")
                sys.exit(1)

        except Exception as e:
            print(f"✗ Test failed: {e}")
            sys.exit(1)
    else:
        # Run main process with workflow integration
        process_tweets(
            format_name=args.format,
            skip_x_post=not args.post_to_x,
            max_posts=args.max_posts
        )
