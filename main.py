import os
import requests
from google import genai

# পরিবেশ ভেরিয়েবল থেকে ক্রেডেনশিয়াল নেওয়া
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def send_telegram_message(text):
    """টেলিগ্রাম চ্যাটে বার্তা পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram message error: {e}")

def get_latest_tokens():
    """DexScreener থেকে সর্বশেষ টোকেন প্রোফাইল ডাটা সংগ্রহ"""
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            return res.json()[:3]  # শীর্ষ ৩টি সাম্প্রতিক টোকেন
    except Exception as e:
        print(f"DexScreener fetch error: {e}")
    return []

def analyze_token_with_gemini(token):
    """জেমিনি এআই দিয়ে বাংলায় রিস্ক ও সেন্টিমেন্ট অ্যানালিসিস তৈরি"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    chain = token.get("chainId", "Unknown")
    token_address = token.get("tokenAddress", "Unknown")
    description = token.get("description", "No description provided.")
    url = token.get("url", "")
    
    prompt = f"""
তুমি একজন ক্রিপ্টোকারেন্সি ও ব্লকচেইন সিকিউরিটি স্পেশালিস্ট।
নিচের নতুন ক্রিপ্টো টোকেন ডাটা পর্যালোচনা করে সম্পূর্ণ বাংলায় একটি 'Risk & Sentiment Analysis' তৈরি করো:

- চেইন/ব্লকচেইন: {chain}
- টোকেন অ্যাড্রেস: {token_address}
- ডেসক্রিপশন: {description}
- লিঙ্ক: {url}

তোমার রিপোর্টটি টেলিগ্রাম মেসেজ উপযোগী সুন্দর ফরম্যাটে বাংলায় লিখবে:
১. টোকেন পরিচিতি ও সারসংক্ষেপ
২. মার্কেট সেন্টিমেন্ট (Positive / Neutral / Negative)
৩. ঝুঁকি ও স্ক্যাম/রাগপুল রিক্স মূল্যায়ন (Low / Medium / High Risk এবং কারণ)
৪. বিনিয়োগকারীদের জন্য সতর্কতা উপদেশ

সবকিছু সহজ ও স্পষ্ট বাংলা ভাষায় লিখবে।
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Gemini analysis error: {e}")
        return f"⚠️ {chain} চেইনের টোকেনের অ্যানালিসিস তৈরিতে সমস্যা হয়েছে।"

def main():
    print("Crypto Radar Bot চালু হচ্ছে...")
    tokens = get_latest_tokens()
    if not tokens:
        print("কোনো নতুন টোকেন পাওয়া যায়নি।")
        return
        
    for token in tokens:
        chain = token.get("chainId", "").upper()
        addr = token.get("tokenAddress", "")
        print(f"অ্যানালিসিস তৈরি হচ্ছে: {chain} - {addr}")
        
        analysis = analyze_token_with_gemini(token)
        
        message = f"🚨 *নতুন ক্রিপ্টো টোকেন রাডার এলার্ট* 🚨\n\n"
        message += f"🔗 *চেইন:* `{chain}`\n"
        message += f"📍 *অ্যাড্রেস:* `{addr}`\n\n"
        message += f"{analysis}\n\n"
        if token.get('url'):
            message += f"🌐 [DexScreener-এ দেখুন]({token.get('url')})"
            
        send_telegram_message(message)

if __name__ == "__main__":
    main()
