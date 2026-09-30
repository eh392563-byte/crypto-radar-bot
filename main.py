import os
import time
import requests
from google import genai

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

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
    """DexScreener থেকে সর্বশেষ ৩টি টোকেন সংগ্রহ"""
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            return res.json()[:3]
    except Exception as e:
        print(f"DexScreener fetch error: {e}")
    return []

def analyze_token_with_gemini(token):
    """Gemini AI দিয়ে বাংলায় অ্যানালিসিস তৈরি (অটো-ফলব্যাক সহ)"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    chain = token.get("chainId", "অজানা")
    token_address = token.get("tokenAddress", "অজানা")
    description = token.get("description", "কোন বিবরণ পাওয়া যায়নি।")
    url = token.get("url", "")

    prompt = f"""
তুমি একজন ক্রিপ্টো সিকিউরিটি স্পেশালিস্ট। নিচের টোকেনটির তথ্য পর্যালোচনা করে সম্পূর্ণ বাংলায় একটি স্পষ্ট অ্যানালিসিস দাও:
- ব্লকচেইন: {chain}
- টোকেন অ্যাড্রেস: {token_address}
- ডেসক্রিপশন: {description}
- লিঙ্ক: {url}

নিচের পয়েন্টগুলো খুব সুন্দর ও সহজ বাংলায় তুলে ধরো:
১. টোকেন পরিচিতি ও সারসংক্ষেপ
২. মার্কেট সেন্টিমেন্ট (ইতিবাচক / নিরপেক্ষ / নেতিবাচক)
৩. ঝুঁকি ও রাগপুল/স্ক্যাম সম্ভাবনা (কম / মাঝারি / উচ্চ ঝুঁকি)
৪. সতর্কতা উপদেশ
"""
    # সার্ভারে চাপ থাকলে একের পর এক মডেল ট্রাই করবে
    models_to_try = ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-2.5-pro"]
    last_error = ""

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue

    return f"⚠️ অ্যানালিসিস তৈরিতে সাময়িক সমস্যা হয়েছে। এরর: {last_error}"

def main():
    tokens = get_latest_tokens()
    if not tokens:
        print("কোনো নতুন টোকেন নেই।")
        return

    for token in tokens:
        chain = str(token.get("chainId", "")).upper()
        addr = token.get("tokenAddress", "")
        
        analysis = analyze_token_with_gemini(token)
        
        message = f"🚨 নতুন ক্রিপ্টো টোকেন রাডার এলার্ট 🚨\n\n"
        message += f"🔗 চেইন: {chain}\n"
        message += f"📍 অ্যাড্রেস: {addr}\n\n"
        message += f"{analysis}\n\n"
        if token.get('url'):
            message += f"🌐 DexScreener লিঙ্ক: {token.get('url')}"
            
        send_telegram_message(message)
        time.sleep(2)  # রেট লিমিট এড়াতে ছোট বিরতি

if __name__ == "__main__":
    main()
