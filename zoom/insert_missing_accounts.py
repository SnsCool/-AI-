#!/usr/bin/env python3
"""ZoomKeysシートにあるがSupabaseに未登録のアカウントを挿入"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
client = create_client(url, key)

accounts = [
    {"assignee": "長谷川小夏", "group": 1, "account_id": "GxIm0isvQtODwk10pbjCkA", "client_id": "L1kMOF4LSiqv8LCRrcKYKg", "client_secret": "8BE6NWfG1gB3sOp35IXeJu74tmxR8Dx5"},
    {"assignee": "根本美沙", "group": 1, "account_id": "Tc6sZhFOR_KPEokO1Mzk0g", "client_id": "yr50N3vWS6OWjF16Ou3Ueg", "client_secret": "Cmg7P7523M5pY6645bPQexiioAG2pA0W"},
    {"assignee": "中村亮祐", "group": 1, "account_id": "9KqVxCj4RNucHv-IclHRyA", "client_id": "soE9H3mZSfKF9DZod4uBA", "client_secret": "VJKG1G3vhdyZfsmQZ8u2UwGbB8kqTxv6"},
    {"assignee": "梅津真珠", "group": 1, "account_id": "xsFk8q46QeOBirEurMHsag", "client_id": "lpP0bdL5RwmQX7TpVjD4mg", "client_secret": "bU3levyJW2uvTMewNPwx04HeHyUQ7unF"},
    {"assignee": "竹内彩華", "group": 2, "account_id": "h5kn7v1ATeivmioqcsw_Vw", "client_id": "1Zhg5ycYSMObWzD84QqKg", "client_secret": "fvhh6IsnqcS6a8E2qy8Ur4xsbG2BcyOG"},
    {"assignee": "和佐田舞緒", "group": 2, "account_id": "vlieHGu5RhGHNrCxq1UtQg", "client_id": "PqlWSj69RySJJ4NwtH1a4w", "client_secret": "byi428c2bM7WZZe2SwcTzqQ6D8xiuxTW"},
    {"assignee": "和樹一樹", "group": 2, "account_id": "yR7xeKNQTT28e5wQK6fkMA", "client_id": "N3hTFr9BTQWV3zCgSkFtVg", "client_secret": "RFI06PgPlVRZ2O8MHsCZK0ltKgtAB48r"},
    {"assignee": "栗原日向子", "group": 2, "account_id": "v2oWZ88BSqqEduk-ZE9waw", "client_id": "xstKYWysSliSKbjXn3oeJw", "client_secret": "kxamIO1727VsspxEVSxKsjDSHLyieGTk"},
    {"assignee": "林愛菜", "group": 3, "account_id": "yD65MMbORPicBYC6CzC16Q", "client_id": "w2ADATHLQguK7gWpn3UsQA", "client_secret": "dqtFisdDnrYiR5AjMbvAbdQhn9Ao9eVa"},
    {"assignee": "野中碧", "group": 3, "account_id": "nbSSgt8PRVWPe4yXWlOpcQ", "client_id": "FVThz6kESzeyZJIMaK_Taw", "client_secret": "j9RmEPqATwfS01Zo4VmPiJ4E3BOllbhM"},
    {"assignee": "坂口武蔵", "group": 3, "account_id": "UAAooVSTQFmSicXqIGbXPA", "client_id": "WOI0JwCBSwq93yMNwquiRQ", "client_secret": "Tfyaa3j5fjCsHC2xnrHH0CVIGN8i0zh5"},
    {"assignee": "根本義暉", "group": 3, "account_id": "fX32FLlkTbml7BPkjF4vdw", "client_id": "Sdond_zRQ7W3OE0uWd7Ryg", "client_secret": "aKz8VfxXs56UTsbBPBel3aEf7IhCUGQ9"},
    {"assignee": "鈴木里果", "group": 4, "account_id": "TECozTcpQS22jZUlgX1wWg", "client_id": "HuCL9453TVW2F89fOJdcg", "client_secret": "XvjqfZ5Zlt165syCIvrsdvP6tEpQWPcD"},
    {"assignee": "遠藤威", "group": 4, "account_id": "HlKK-h5NSACZtAeZTAjVDw", "client_id": "coXv5SltSHuqWWX_zLYbiw", "client_secret": "dIHv3ezqon2SEgUj524kVF97SiLY5Ytk"},
    {"assignee": "鎌田夕季", "group": 4, "account_id": "ayXZwkRKTfmBXPSkyA6ghA", "client_id": "tCOIH7XR2elass28l_sEw", "client_secret": "67koGEz61I5PXXK2WZvr4SSqCwTqnEiT"},
    {"assignee": "大谷みくに", "group": 4, "account_id": "gA8z7hjoRkGjXYtI5YDIYA", "client_id": "zeDjVlx6RoWL49PYnDLPx", "client_secret": "O4uvmDLbluUtLShlsP9zgHRkXHvYbN6D"},
    {"assignee": "森田主", "group": 5, "account_id": "VZRJj_aBQeCBoVLFiF6CoA", "client_id": "eSPw_jxQQHSjlXTRJp8gmQ", "client_secret": "EPjtSMICmntwzrhho2hzxDUmdarEzlPn"},
    {"assignee": "上村勇人", "group": 5, "account_id": "QnNR-VNKQvu4LYFAaG3stQ", "client_id": "ec35lOV5RbCsFmwV0UF0hg", "client_secret": "Ry5sJJzf8h05hMyMxcnJtX2K2Fvbqfs7"},
    {"assignee": "石岡涼", "group": 5, "account_id": "5BsyOKLTQIGMtkkybCht_g", "client_id": "e19BMh2MQam6blF_xCzbWg", "client_secret": "W2O3I17cLRcOWwtUfZzQA3qAG2aJATSS"},
    {"assignee": "杉井友紀", "group": 5, "account_id": "_7fH2MyaR2y503qcBzmwHQ", "client_id": "Fl4ve1U8SqamZxn9HZVZOA", "client_secret": "mYytDugOhyxqhf432U2qZEh5hxjCwEcy"},
    {"assignee": "青木孝", "group": 6, "account_id": "YHdHi0VqTlK5XjPaPskw0g", "client_id": "Hoo9kL5DSfy62JMzW0HtOQ", "client_secret": "GAMXWQyCNeVxRW1ujBTKeQrFetUAgGgf"},
    {"assignee": "五十嵐凌大", "group": 6, "account_id": "juwUI1iOToSPQlzgtkpJAg", "client_id": "dgbHkGjKSl6IK7KWd0mvyg", "client_secret": "umw41G904xmVojKbpFJtTXt9btLiJGzz"},
    {"assignee": "竹中蒼太", "group": 6, "account_id": "MCSflJM3RAOKRniFcwIA8A", "client_id": "Pfb788pIQEij7jZczKM3Sg", "client_secret": "Fpb5nH5wnGvOaNbt3rrz6M1gMyEb4Coy"},
    {"assignee": "山本美結", "group": 6, "account_id": "appRyanoTLCZVo4A4sMJOQ", "client_id": "eNTafILYRgG6Icp6EXnWrg", "client_secret": "yMyYbqzDZ51VsSx5MncaNciH0gMIDV3z"},
]

def main():
    print(f"Supabase URL: {url}")
    print(f"挿入するアカウント数: {len(accounts)}")
    print()

    success_count = 0
    error_count = 0

    for account in accounts:
        try:
            result = client.table("zoom_accounts").upsert(account, on_conflict="assignee").execute()
            print(f"✅ {account['assignee']}")
            success_count += 1
        except Exception as e:
            print(f"❌ {account['assignee']}: {e}")
            error_count += 1

    print()
    print(f"完了: 成功 {success_count}件, エラー {error_count}件")

if __name__ == "__main__":
    main()
