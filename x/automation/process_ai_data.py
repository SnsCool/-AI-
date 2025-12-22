#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI関連投稿データ処理スクリプト
Apifyで取得したデータを分析用に整形
"""

import json
import os
import sys
from datetime import datetime
import re

def process_ai_data(input_dir, output_dir):
    """AI関連投稿データを処理"""
    
    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 処理対象ファイルを検索
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    if not json_files:
        print("処理対象のJSONファイルが見つかりません")
        return
    
    # データを統合
    all_posts = []
    ai_keywords = ['AI', 'artificial intelligence', 'machine learning', 'deep learning', 
                   'LLM', 'GPT', 'Claude', 'ChatGPT', 'AI model', 'neural network']
    
    for json_file in json_files:
        file_path = os.path.join(input_dir, json_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # AI関連の投稿のみフィルタリング
            for post in data:
                text = post.get('text', '').lower()
                if any(keyword.lower() in text for keyword in ai_keywords):
                    all_posts.append(post)
                    
        except Exception as e:
            print(f"ファイル処理エラー: {json_file} - {e}")
            continue
    
    # データを保存
    date_str = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(output_dir, f'ai_trends_{date_str}.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# AI関連投稿データ - {date_str}\n\n")
        f.write(f"取得件数: {len(all_posts)}件\n")
        f.write(f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, post in enumerate(all_posts, 1):
            f.write(f"## 投稿 {i}\n")
            f.write(f"**アカウント**: {post.get('user', {}).get('username', 'N/A')}\n")
            f.write(f"**いいね数**: {post.get('likeCount', 0)}\n")
            f.write(f"**リツイート数**: {post.get('retweetCount', 0)}\n")
            f.write(f"**投稿日時**: {post.get('createdAt', 'N/A')}\n")
            f.write(f"**内容**: {post.get('text', 'N/A')}\n")
            f.write(f"**URL**: {post.get('url', 'N/A')}\n\n")
    
    print(f"AI関連投稿データを保存しました: {output_file}")
    print(f"処理件数: {len(all_posts)}件")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: python3 process_ai_data.py <input_dir> <output_dir>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    process_ai_data(input_dir, output_dir)
