import requests
import getpass
from datetime import datetime

def get_user_credentials():
    """طلب بيانات الدخول من المستخدم"""
    print("\n🔐 أدخل بيانات تسجيل الدخول")
    print("-" * 30)
    
    while True:
        phone = input("📱 رقم الهاتف (مثال: 01025117350): ").strip()
        if phone and phone.isdigit() and len(phone) == 11:
            break
        print("❌ الرجاء إدخال رقم هاتف صحيح (11 رقم)")
    
    # استخدام getpass لإخفاء كلمة المرور أثناء الكتابة
    password = getpass.getpass("🔑 كلمة المرور (لن تظهر أثناء الكتابة): ").strip()
    
    if not password:
        print("❌ يجب إدخال كلمة المرور")
        return None, None
    
    return phone, password

def login(phone, password):
    """تسجيل الدخول للحصول على التوكن"""
    url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    
    payload = {
        'grant_type': "password",
        'username': phone,
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
        'digitalId': "25VT5Q5QWG8DK",
        'device-id': "b26ba335813fad21"
    }
    
    try:
        print("⏳ جاري تسجيل الدخول...")
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        access_token = data.get('access_token')
        
        if access_token:
            print("✅ تم تسجيل الدخول بنجاح")
            return access_token
        else:
            print("❌ فشل في الحصول على التوكن")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return None
    except Exception as e:
        print(f"❌ خطأ في تسجيل الدخول: {e}")
        return None

def get_consumption_data(token, phone):
    """جلب بيانات الاستهلاك"""
    url = "https://mobile.vodafone.com.eg/services/dxl/usage/usageConsumptionReport"
    
    params = {
        '@type': "aggregated",
        'bucket.product.publicIdentifier': phone
    }
    
    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'api-host': "usageConsumptionHost",
        'useCase': "aggregated",
        'Authorization': f"Bearer {token}",
        'api-version': "v2",
        'device-id': "b26ba335813fad21",
        'x-agent-operatingsystem': "15",
        'clientId': "AnaVodafoneAndroid",
        'x-agent-device': "Samsung SM-A165F",
        'x-agent-version': "2025.12.2",
        'x-agent-build': "1080",
        'msisdn': phone,
        'Content-Type': "application/json",
        'Accept-Language': "ar"
    }
    
    try:
        print("⏳ جاري جلب بيانات الاستهلاك...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return None
    except Exception as e:
        print(f"❌ خطأ في جلب البيانات: {e}")
        return None

def extract_data(consumption_data):
    """استخراج البيانات المطلوبة"""
    if not consumption_data:
        return None
    
    # رصيد المال المتبقي (من فئة Tariff)
    remaining_balance = None
    for item in consumption_data:
        if item.get("@type") == "Tariff":
            for bucket in item.get("bucket", []):
                for balance in bucket.get("bucketBalance", []):
                    if balance.get("@type") == "Remaining" and balance.get("remainingValue", {}).get("units") == "LE":
                        remaining_balance = balance["remainingValue"]
                        break
    
    # الفليكسات المتبقية وفليكسات الشهر الجديد والماني باك
    flex_remaining = None
    next_cycle_flex = None
    money_back = None
    family_flex = None
    flex_renewal_date = None
    family_minutes = None
    
    for item in consumption_data:
        item_type = item.get("@type", "")
        
        # فئة FLEX (الفليكسات العائلية)
        if item_type == "FLEX":
            for bucket in item.get("bucket", []):
                if bucket.get("usageType") == "flex":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            family_flex = balance["remainingValue"]
                            # استخراج تاريخ التجديد إذا موجود
                            valid_for = balance.get("validFor")
                            if valid_for and valid_for.get("endDateTime"):
                                flex_renewal_date = valid_for["endDateTime"]
        
        # فئة OTHERS
        elif item_type == "OTHERS":
            for bucket in item.get("bucket", []):
                usage_type = bucket.get("usageType", "")
                
                # الفليكسات المتبقية (حالي) - count
                if usage_type == "count":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            flex_remaining = balance["remainingValue"]
                
                # فليكسات الشهر الجديد (Limit)
                elif usage_type == "limit":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            next_cycle_flex = balance["remainingValue"]
                
                # دقائق العائلة
                elif usage_type == "mins":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            family_minutes = balance["remainingValue"]
                
                # الماني باك المتبقي
                elif usage_type == "money":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            money_back = balance["remainingValue"]
    
    return {
        "remaining_balance": remaining_balance,
        "flex_remaining": flex_remaining,
        "next_cycle_flex": next_cycle_flex,
        "money_back": money_back,
        "family_flex": family_flex,
        "flex_renewal_date": flex_renewal_date,
        "family_minutes": family_minutes
    }

def format_date(date_str):
    """تنسيق التاريخ"""
    if not date_str:
        return "غير محدد"
    
    try:
        # تحويل من "2026-02-02T00:00:00.000+0000" إلى "2 فبراير 2026"
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+0000', '+00:00'))
        # تنسيق التاريخ بالعربية
        month_names = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
            5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }
        day = dt.day
        month = month_names.get(dt.month, dt.month)
        year = dt.year
        return f"{day} {month} {year}"
    except:
        return date_str

def display_results(data, phone):
    """عرض البيانات بشكل منظم"""
    print("\n" + "="*60)
    print(f"📱 استهلاك فودافون مصر - {phone}")
    print("="*60)
    
    # قسم الرصيد المالي
    print("\n💰 الرصيد المالي:")
    print("-" * 30)
    if data["remaining_balance"]:
        amount = data["remaining_balance"]["amount"]
        unit = data["remaining_balance"]["units"]
        print(f"💵 الرصيد المتبقي: {amount} {unit}")
    else:
        print("❌ لم يتم العثور على الرصيد المتبقي")
    
    # قسم الفليكسات
    print("\n📊 الفليكسات:")
    print("-" * 30)
    
    # الفليكسات العائلية
    if data["family_flex"]:
        amount = data["family_flex"]["amount"]
        unit = data["family_flex"]["units"]
        print(f"👨‍👩‍👧‍👦 فليكساتك الحالية {amount} {unit}")
        
        # تاريخ التجديد
        renewal_date = format_date(data["flex_renewal_date"])
        print(f"🗓️  تاريخ التجديد: {renewal_date}")
    else:
        print("❌ الباقة انتهت او الفليكسات خلصت")
    
    # الفليكسات العادية
    if data["flex_remaining"]:
        amount = data["flex_remaining"]["amount"]
        unit = data["flex_remaining"]["units"]
        print(f"📱 الفليكسات المتبقية: {amount} {unit}")
    else:
        print("❌ لم يتم العثور على الفليكسات المتبقية")
    
    # فليكسات الشهر الجديد
    if data["next_cycle_flex"]:
        amount = data["next_cycle_flex"]["amount"]
        unit = data["next_cycle_flex"]["units"]
        print(f"🎁 فليكسات الشهر الجديد: {amount} {unit}")
    
    # قسم الدقائق
    print("\n⏰ الدقائق:")
    print("-" * 30)
    if data["family_minutes"]:
        amount = data["family_minutes"]["amount"]
        unit = data["family_minutes"]["units"]
        print(f"📞 دقائق العائلة المتبقية: {amount} {unit}")
    else:
        print("❌ لم يتم العثور على دقائق العائلة")
    
    # قسم الماني باك
    print("\n💳 الماني باك:")
    print("-" * 30)
    if data["money_back"]:
        amount = data["money_back"]["amount"]
        unit = data["money_back"]["units"]
        print(f"💰 الماني باك المتبقي: {amount} {unit}")
    else:
        print("❌ لم يتم العثور على الماني باك المتبقي")
    
    print("\n" + "="*60)
    
    # ملخص سريع
    print("\n📋 الملخص السريع:")
    print("-" * 30)
    
    summary_items = []
    if data["remaining_balance"]:
        summary_items.append(f"💰 {data['remaining_balance']['amount']} جنيه")
    if data["family_flex"]:
        summary_items.append(f"👪 {data['family_flex']['amount']} فليكس عائلي")
    if data["flex_remaining"]:
        summary_items.append(f"📱 {data['flex_remaining']['amount']} فليكس عادي")
    if data["family_minutes"]:
        summary_items.append(f"⏰ {data['family_minutes']['amount']} دقيقة")
    if data["money_back"]:
        summary_items.append(f"💳 {data['money_back']['amount']} ماني باك")
    
    if summary_items:
        for item in summary_items:
            print(f"✅ {item}")
    else:
        print("❌ لا توجد بيانات متاحة للعرض")
    
    print("="*60)

def main():
    """الدالة الرئيسية"""
    print("="*60)
    print("     نظام استعلام استهلاك فودافون مصر     ")
    print("="*60)
    
    # محاولة لثلاث مرات في حالة فشل الدخول
    for attempt in range(1, 4):
        print(f"\nالمحاولة {attempt} من 3")
        
        # طلب بيانات الدخول
        phone, password = get_user_credentials()
        if not phone or not password:
            continue
        
        # تسجيل الدخول
        token = login(phone, password)
        
        if token:
            # جلب بيانات الاستهلاك
            consumption_data = get_consumption_data(token, phone)
            
            if consumption_data:
                # استخراج وعرض البيانات
                extracted_data = extract_data(consumption_data)
                if extracted_data:
                    display_results(extracted_data, phone)
                    break
                else:
                    print("❌ لم يتم استخراج البيانات المطلوبة")
            else:
                print("❌ فشل في جلب بيانات الاستهلاك")
        else:
            print("❌ فشل تسجيل الدخول. تحقق من الرقم وكلمة المرور")
        
        if attempt < 3:
            retry = input("\nهل تريد إعادة المحاولة؟ (نعم/لا): ").strip().lower()
            if retry not in ['نعم', 'ن', 'yes', 'y']:
                break
    
    print("\nشكراً لاستخدامك البرنامج! 👋")

# تشغيل البرنامج
if __name__ == "__main__":
    main()