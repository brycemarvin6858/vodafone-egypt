
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
import string

red_color = '\033[1;31m'
white_color = '\033[1;97m'
light_blue_color = '\033[1;36m'
light_green_color = '\033[1;32m'
yellow_color = '\033[1;33m'

def generation_link(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def get_authorization(number, password):
    """دالة تسجيل دخول الأونر والحصول على التوكن باستخدام API الجديد"""
    
    print(light_blue_color, f"🔄 جاري تسجيل الدخول للرقم: {number}")
    
    url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    
    payload = {
        'grant_type': "password",
        'username': number,
        'password': password,
        'client_secret': "95fd95fb-7489-4958-8ae6-d31a525cd20a",
        'client_id': "ana-vodafone-app"
    }
    
    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip",
        'silentLogin': "true",
        'x-agent-operatingsystem': "15",
        'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "ar",
        'x-agent-device': "Samsung SM-A165F",
        'x-agent-version': "2025.12.2",
        'x-agent-build': "1080",
        'digitalId': generation_link(13),  # توليد digitalId عشوائي
        'device-id': generation_link(16)   # توليد device-id عشوائي
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'access_token' in data:
                jwt = data['access_token']
                print(light_green_color, f"✅ تم تسجيل الدخول بنجاح للرقم: {number}")
                return "Bearer " + jwt
            else:
                print(red_color, f"❌ ({number}) فشل في الحصول على التوكن")
                print(red_color, f"❌ الاستجابة: {data}")
                return "error"
        else:
            print(red_color, f"❌ ({number}) خطأ في تسجيل الدخول - كود الخطأ: {response.status_code}")
            print(red_color, f"❌ تفاصيل الخطأ: {response.text}")
            return "error"
            
    except requests.exceptions.Timeout:
        print(red_color, f"❌ ({number}) انتهت مهلة الاتصال")
        return "error"
    except requests.exceptions.RequestException as e:
        print(red_color, f"❌ ({number}) خطأ في الاتصال: {e}")
        return "error"
    except Exception as e:
        print(red_color, f"❌ ({number}) خطأ غير متوقع: {e}")
        return "error"

def getFlexes(token, n):
    """دالة الحصول على نسبة الفليكس"""
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'EN',
        'Authorization': token,
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Referer': 'https://web.vodafone.com.eg/spa/familySharing',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'clientId': 'WebsiteConsumer',
        'msisdn': n,
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    try:
        response = requests.get(
            f'https://web.vodafone.com.eg/services/dxl/usage/usageConsumptionReport?bucket.product.publicIdentifier={n}&@type=aggregated',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()

            for item in data:
                if item.get("@type") == "OTHERS":
                    for bucket in item.get("bucket", []):
                        if bucket.get("usageType") == "limit":
                            for balance in bucket.get("bucketBalance", []):
                                if balance.get("@type") == "Remaining" and balance["remainingValue"]["units"] == "FLEX":
                                    flex_amount = balance["remainingValue"]["amount"]
                                    return flex_amount
            
            return None
            
        elif response.status_code == 401:
            print(red_color, "❌ التوكن منتهي الصلاحية أو غير صالح")
            return None
        else:
            print(red_color, f"❌ خطأ في الاستعلام: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print(red_color, "❌ انتهت مهلة الاتصال أثناء الاستعلام عن الفليكس")
        return None
    except Exception as e:
        print(red_color, f"❌ خطأ أثناء الاستعلام عن الفليكس: {e}")
        return None

def main():
    print(light_blue_color, '👋 أهلاً بك في نظام معرفة نسبة الفليكس!')
    print('-' * 50)
    
    # إدخال البيانات
    owner_number = input("📱 رقم الأونر: ")
    owner_password = input("🔑 كلمة سر الأونر: ")
    
    print("\n" + "="*50)
    
    # تسجيل الدخول باستخدام API الجديد
    token = get_authorization(owner_number, owner_password)
    
    if token != "error":
        
        # الحصول على النسبة باستخدام الطريقة الأصلية
        flex_balance = getFlexes(token, owner_number)
        
        # إذا فشلت الطريقة الأصلية، جرب الطريقة البديلة
        if flex_balance is None:
            flex_balance = getFlexes_alternative(token, owner_number)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if flex_balance is not None:
            print(light_green_color, f"🎯 نسبة الفليكس الحالية: {flex_balance} فليكس")
 
            
if __name__ == "__main__":
    main()