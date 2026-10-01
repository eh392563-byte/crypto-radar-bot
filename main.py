import os
import requests
from groq import Groq

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def send_telegram_message(text):
    """টেলিগ্রাম চ্যাটে বার্তা পাঠানো"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram error: {e}")

def get_latest_tokens():
    """DexScreener থেকে সর্বশেষ ১টি টোকেন সংগ্রহ"""
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            return res.json()[:1]
    except Exception as e:
        print(f"DexScreener fetch error: {e}")
    return []

def analyze_token_with_groq(token):
    """Groq openai/gpt-oss-120b দিয়ে বাংলায় সরাসরি সিকিউরিটি অ্যানালিসিস তৈরি"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        chain = token.get("chainId", "অজানা")
        token_address = token.get("tokenAddress", "অজানা")
        description = token.get("description", "কোন বিবরণ পাওয়া যায়নি।")
        url = token.get("url", "")

        prompt = f"""
তুমি একজন ক্রিপ্টো সিকিউরিটি স্পেশালিস্ট। নিচের নতুন টোকেনটির তথ্য ভালো করে পর্যালোচনা করে সম্পূর্ণ বাংলায় একটি স্পষ্ট অ্যানালিসিস দাও:
- ব্লকচেইন: {chain}
- টোকেন অ্যাড্রেস: {token_address}
- ডেসক্রিপশন: {description}
- লিঙ্ক: {url}

নিচের পয়েন্টগুলো খুব সুন্দর ও সহজ বাংলায় তুলে ধরো:
১. টোকেন পরিচিতি ও উদ্দেশ্য
২. মার্কেট সেন্টিমেন্ট (ইতিবাচক / নিরপেক্ষ / নেতিবাচক)
৩. রাগপুল ও স্ক্যাম ঝুঁকি (কম / মাঝারি / অতি উচ্চ ঝুঁকি)
৪. সতর্কতা উপদেশ
"""
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="openai/gpt-oss-120b",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ অ্যানালিসিস তৈরিতে সমস্যা হয়েছে: {e}"

def main():
    tokens = get_latest_tokens()
    if not tokens:
        print("কোনো নতুন টোকেন নেই।")
        return

    for token in tokens:
        chain = str(token.get("chainId", "")).upper()
        addr = token.get("tokenAddress", "")
        
        analysis = analyze_token_with_groq(token)
        
        message = f"🚨 নতুন ক্রিপ্টো টোকেন রাডার এলার্ট 🚨\n\n"
        message += f"🔗 চেইন: {chain}\n"
        message += f"📍 অ্যাড্রেস: {addr}\n\n"
        message += f"{analysis}\n\n"
        if token.get('url'):
            message += f"🌐 DexScreener লিঙ্ক: {token.get('url')}"
            
        send_telegram_message(message)

if __name__ == "__main__":
    main()
