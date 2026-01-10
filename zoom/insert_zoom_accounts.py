#!/usr/bin/env python3
"""
32件のZoomアカウントをSupabaseに挿入
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Supabaseクライアント
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
client = create_client(url, key)

# 32件のZoomアカウントデータ
accounts = [
    {"assignee": "山口有紗", "account_id": "gQ-vOgB4S7CYYJjh4YJWtQ", "client_id": "66yPv8XTHaf6QWd7dcehg", "client_secret": "rXEQ4uqtaxvx79dAb4aba24sKOUpIar2"},
    {"assignee": "長谷川太一", "account_id": "08_p6hrLQIKYlVVR07fFWQ", "client_id": "mQY2_ACTQ4iti9aZTOj5hA", "client_secret": "LOC2A3rrR1nFrDGU5IZCHAswNXAxVQi7"},
    {"assignee": "藤井準也", "account_id": "V3pBYs3sQR26xHqnb9ggqQ", "client_id": "YwPFuX1bTWqLUqaJCg3U7Q", "client_secret": "5nJGGVvzJ6zXQPQaGsqY2D44yfDCGjRu"},
    {"assignee": "中村珠梨", "account_id": "HnZ3uyTvSIKJj_TyJoTnhg", "client_id": "8Y8qL8B_QU2b3l_1RJR6Sw", "client_secret": "iDcg4Pv0qRwSuPLX9tywKIR1W8VwG2Nc"},
    {"assignee": "西清那", "account_id": "nCaA9veoSFCt1V0pHc13zg", "client_id": "UZFGMHLxRVSklk0ZqJNBdQ", "client_secret": "XSG8Y2SUHVTLaHHVCPCvKT9X6R0wpWqU"},
    {"assignee": "渋谷桃子", "account_id": "7dpY94Z_Q3i4cTXE5fLHjA", "client_id": "6h1AWEoGQF61BN1xSKLnHw", "client_secret": "3PW9e29Fq5x7xfO50n2PN1bvpFXGxLhH"},
    {"assignee": "清水玲央", "account_id": "dGnMcRrtShG-2sJHKbqThg", "client_id": "Y1iiWPAISYqCXdqN0WnBjQ", "client_secret": "5pR0nwqGUDl6bZfM7yEEeDY6aR5z8LB3"},
    {"assignee": "苙隼人", "account_id": "4MjqWCH4ScKWaXlOLePxUA", "client_id": "Td3eUfMhQBK3j4R4kPGEWg", "client_secret": "9BLzowNXvjjfwc1uxYBNaOWWXKsMSQWh"},
    {"assignee": "日下真由子", "account_id": "gAhw_YYIRr6aG2PJ9l2xxg", "client_id": "wvl4JLV3Q_mYdqkLBfQv2w", "client_secret": "6VJB66HVYjXNDmv9WnqPz9FH6IjxbYwf"},
    {"assignee": "森田咲音", "account_id": "bTB7SHzARx6Ym3jGz3TjfA", "client_id": "qb1xSjhBSIWOVFTq3IlQ", "client_secret": "HVWLqc4fHDxrZYpxl17aFZXXDVu5sFwb"},
    {"assignee": "播磨谷 彩", "account_id": "6Yb-YoNiQxGCbLGF2S8ywg", "client_id": "JDPxRxXoTl2bLq-b-Bl5cw", "client_secret": "a3oVsPCrJDjL2WrxqLXA8FTAaE09H9N4"},
    {"assignee": "千葉大雅", "account_id": "Q6-JDKD5RYKT-WlLGrb2vQ", "client_id": "G_3CljbZSQqEAjdFLwcIFQ", "client_secret": "oJhqVB1S0pqhBFbFGdmO5HlI8MG3w4xo"},
    {"assignee": "雨宮令奈", "account_id": "0RKM6ZuCRq-QCeCUxQYKWA", "client_id": "JpcVdSz_TXaD4rZvfVGXcg", "client_secret": "rOmvnLplVcFI1kfcOHwNK0hJkJcm8TLT"},
    {"assignee": "梅村章", "account_id": "rW2fhgKWSaeTz1a6HscxAg", "client_id": "J6WCkE7RDKf9Z70RHLzw", "client_secret": "FhNGJH94DmLXlqUMuRJGsJMaOTpmFZCI"},
    {"assignee": "有川薫", "account_id": "A_v4QrfaQkO-tVBxH1VwdQ", "client_id": "fIKwcl5lQLCC_NMqDy-xBw", "client_secret": "uiqiCkjA89UatJnU3DvmPfR0mQNHuPhf"},
    {"assignee": "持木玲那", "account_id": "f_A4aFewS5ug-VRvmWzj2A", "client_id": "Jg8i03o_ToSGC-OPT0nKog", "client_secret": "1o10HfixsU0YBM2HB2R6CJneMrLJRxcv"},
    {"assignee": "橋口陽香里", "account_id": "eLEaYjfqSbmNy2Sv3JJqtw", "client_id": "7VguqB1pRlm1Zuo24AEBUQ", "client_secret": "e1MnCWDwGjOiCrT1NLsHdmKYqH9FMGTd"},
    {"assignee": "真崎ほのか", "account_id": "16OBqhZMS7-FXkL3SXNS3A", "client_id": "c1e_CwRSEaOG3J7l9cJHA", "client_secret": "9xqIwdAuYWP3cHDWz2FcLBqrjpLamwB8"},
    {"assignee": "横山結衣", "account_id": "QyxJ0_wXTruxXCOQP3UoFA", "client_id": "FXA8a0IbQzmgS94y4lFn2A", "client_secret": "xdE5p5KrqpFLHC6y0hcZv8Rb7VrFJIpe"},
    {"assignee": "義永苑子", "account_id": "RJOFy1HbTuqFn8cH8IvAtg", "client_id": "daTaWDLeSMC4sM2cV27HAg", "client_secret": "fLGpP9VhF3cQjnNuWgJpJgBMJ5E9ufmK"},
    {"assignee": "小森美智子", "account_id": "HCZqASQVQYmFLNgK8u6jTw", "client_id": "4lZUOFm9Tc6OBuD5NwkDhA", "client_secret": "YlWbfNIvJiRHC9cS1DQ0dpV0YPFJ0Nqj"},
    {"assignee": "成勢将司", "account_id": "IfvuPfCRRdGBmqEkP8kQNg", "client_id": "JOZ_2yBkR6W-mxSqbKp-Eg", "client_secret": "KzBBz2SFGNTilYEKNBfNwOYZqGCFCRZi"},
    {"assignee": "楠瀬龍海", "account_id": "0TqNO_HWSNKnYhNZLh7OHg", "client_id": "RLilQhQYQpG1bUXXwLTLmA", "client_secret": "SFGNWIDbFmTm4lPHN0LmJMpMZZb0H0yN"},
    {"assignee": "笠松佑衣", "account_id": "LQzjIZ2sRi2iOMt2ntYFew", "client_id": "Mz7HqmqORnWdBQ2n_cGFnA", "client_secret": "2pEoE2TKl4LGnB5oflGLBP5qgjRq0tPR"},
    {"assignee": "栗原瑠人", "account_id": "Dc4F1Y3mS0yqQ-38AcfV9w", "client_id": "7iqNVf5qTWiYHHBqZ3GHCQ", "client_secret": "IwO5WFJvk5n9saBKqRu0xeaAfrcQQhQh"},
    {"assignee": "長谷川こなつ", "account_id": "e4Eg-Qf4S0uE_l6QFILKXw", "client_id": "S6nScHpGRUi3i6WllMJ2hw", "client_secret": "OmBmJJNE4UOuiUWcmAnXFuBLLvRmq8Go"},
    {"assignee": "濵田稜大", "account_id": "2TxJMHPXQCahqKqVOJLn9g", "client_id": "2AYTYMYySxiCclIhbRCrNw", "client_secret": "WLdB4nIfJnWRcBb2Ge0UKoSJpzuhUzh6"},
    {"assignee": "山崎春花", "account_id": "oXAAlqDcSKmuqfHi5c5mWA", "client_id": "ZhXQw3sERu6JEkR4FqLAdg", "client_secret": "pzzwqsJVxzxIJzaWNYM6Gq2C15o2hJBh"},
    {"assignee": "林清弘", "account_id": "n3l4mjLUTyW0OVDxI7fYCA", "client_id": "DqDlhyTlT72rrDsVnLWAtg", "client_secret": "K6qoJPKDJLCYl4M7cRyDPT69d2TBgSHN"},
    {"assignee": "西岡駿", "account_id": "YWlVlXOURMGWPDk0ZH3TjQ", "client_id": "vTk6XZtGQSuPAlLp65aqZg", "client_secret": "xQcMc4D3VEWChW1jDaycW5rXA4gMJwBK"},
    {"assignee": "陶器尚宏", "account_id": "Sm3m8rxPSTqTuR_PbbKE5w", "client_id": "VVqG2npqSQOKVRnSTOGNw", "client_secret": "dOJpKXnzW8z5OKy4WOlb1kqIoZ63JLRc"},
    {"assignee": "飯塚有紀", "account_id": "C2MzlQlKRpGhkwz0HkGKqA", "client_id": "wWAEuZhkSR2d6AjWN2JrYg", "client_secret": "IeK2YKA79xVLfaC5AWCDR8wQgaXJdP4G"},
]

def main():
    print(f"Supabase URL: {url}")
    print(f"挿入するアカウント数: {len(accounts)}")
    print()

    success_count = 0
    error_count = 0

    for account in accounts:
        try:
            result = client.table("zoom_accounts").insert(account).execute()
            print(f"✅ {account['assignee']}")
            success_count += 1
        except Exception as e:
            # 既に存在する場合はupsertを試みる
            try:
                result = client.table("zoom_accounts").upsert(account, on_conflict="assignee").execute()
                print(f"🔄 {account['assignee']} (更新)")
                success_count += 1
            except Exception as e2:
                print(f"❌ {account['assignee']}: {e2}")
                error_count += 1

    print()
    print(f"完了: 成功 {success_count}件, エラー {error_count}件")

if __name__ == "__main__":
    main()
