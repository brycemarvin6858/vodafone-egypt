import requests
import json
import re

def login(username, password):
    """تسجيل الدخول والحصول على التوكن - API الموبايل"""
    print("⏳ جاري تسجيل الدخول...")
    
    url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    
    payload = {
        'grant_type': "password",
        'username': username,
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
        'digitalId': "2BHAXCXG8IHJZ",
        'device-id': "b26ba335813fad21"
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        print("✅ تم تسجيل الدخول بنجاح")
        return data['access_token']
    except requests.exceptions.RequestException as e:
        print(f"❌ فشل تسجيل الدخول: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"الرد: {e.response.text}")
        return None

def get_flex_products_mobile(msisdn, token):
    """جلب منتجات Flex باستخدام API الموبايل"""
    print("⏳ جاري جلب معلومات الباقات من تطبيق الموبايل...")
    
    url = "https://mobile.vodafone.com.eg/services/dxl/pim/product"
    
    params = {
        'relatedParty.id': msisdn,
        '@type': "FlexProfile"
    }
    
    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'api-host': "ProductInventoryManagementHost",
        'useCase': "FlexProfile",
        'Authorization': f"Bearer {token}",
        'api-version': "v2",
        'device-id': "b26ba335813fad21",
        'x-agent-operatingsystem': "15",
        'clientId': "AnaVodafoneAndroid",
        'x-agent-device': "Samsung SM-A165F",
        'x-agent-version': "2026.1.1",
        'x-agent-build': "1090",
        'msisdn': msisdn,
        'Content-Type': "application/json",
        'Accept-Language': "ar"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        products = response.json()
        
        print(f"✅ تم جلب {len(products)} منتج/خدمة من تطبيق الموبايل")
        return products
            
    except requests.exceptions.RequestException as e:
        print(f"❌ فشل جلب معلومات الباقات: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"كود الخطأ: {e.response.status_code}")
            print(f"الرد: {e.response.text}")
        return None

def is_main_bundle(bundle):
    """التحقق إذا كانت الباقة هي الباقة الرئيسية"""
    
    bundle_id = bundle.get('id', '')
    bundle_name = bundle.get('productSpecification', {}).get('name', '')
    
    # الكشف عن نمط Flex_20**_** (زي Flex_2021_523)
    flex_pattern = r'Flex_20\d{2}_\d+'
    if re.search(flex_pattern, bundle_id):
        return True
    
    # الكشف عن أسماء الباقات المعروفة
    main_keywords = ['فليكس', 'Flex', 'باقة']
    name_match = any(keyword in bundle_name for keyword in main_keywords)
    
    # لازم يكون فيه productPrice (سعر)
    has_price = len(bundle.get('productPrice', [])) > 0
    
    return name_match and has_price

def find_main_bundle_auto(products):
    """البحث التلقائي عن الباقة الرئيسية"""
    
    print("\n🔍 البحث التلقائي عن الباقة الرئيسية...")
    
    main_bundles = []
    
    for product in products:
        if product.get('productPrice'):
            product_id = product.get('id')
            product_name = product.get('productSpecification', {}).get('name', '')
            enc_id = product.get('productOffering', {}).get('encProductId')
            description = product.get('description', '')
            
            prices = []
            for price in product.get('productPrice', []):
                if price.get('price', {}).get('taxIncludedAmount', {}).get('value'):
                    prices.append({
                        'value': price['price']['taxIncludedAmount']['value'],
                        'type': price.get('priceType'),
                        'period': price.get('recurringChargePeriod')
                    })
            
            bundle_info = {
                'id': product_id,
                'name': product_name,
                'description': description,
                'encProductId': enc_id,
                'prices': prices,
                'full_product': product
            }
            
            main_bundles.append(bundle_info)
    
    if not main_bundles:
        print("⚠️ لم يتم العثور على أي باقات")
        return None
    
    # عرض جميع الباقات
    print(f"\n📊 تم العثور على {len(main_bundles)} باقة:")
    for i, bundle in enumerate(main_bundles, 1):
        print(f"\n{i}. {bundle['name']}")
        print(f"   - معرف الباقة: {bundle['id']}")
        for price in bundle['prices']:
            print(f"   - السعر: {price['value']} جنيه")
    
    # البحث عن الباقة الرئيسية
    selected_bundle = None
    for bundle in main_bundles:
        if is_main_bundle(bundle):
            selected_bundle = bundle
            break
    
    # لو ملقتش، اختار أعلى سعر
    if not selected_bundle and main_bundles:
        sorted_bundles = sorted(main_bundles, 
                               key=lambda x: float(x['prices'][0]['value']) if x['prices'] else 0, 
                               reverse=True)
        selected_bundle = sorted_bundles[0]
        print(f"\n🤖 تم اختيار الباقة تلقائياً (أعلى سعر): {selected_bundle['name']}")
    
    if selected_bundle:
        print(f"\n✅✅ الباقة المختارة تلقائياً:")
        print(f"   - {selected_bundle['name']}")
        print(f"   - المعرف: {selected_bundle['id']}")
        return selected_bundle
    else:
        print("❌ لم يتم العثور على باقة رئيسية")
        return None

def renew_flex_bundle_mobile(msisdn, token, bundle):
    """تجديد باقة Flex باستخدام API الموبايل - بنفس نظام جلب البيانات"""
    
    bundle_id = bundle['id']
    bundle_name = bundle['name']
    enc_product_id = bundle['encProductId']
    
    price_info = ""
    if bundle['prices']:
        price_info = f" ({bundle['prices'][0]['value']} جنيه)"
    
    print(f"\n⏳ جاري محاولة تجديد الباقة: {bundle_name}{price_info}...")
    
    # نغير الـ URL لنسخة الموبايل
    url = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
    
    # نفس الـ payload
    payload = {
        "channel": {
            "name": "MobileApp"
        },
        "orderItem": [
            {
                "action": "repurchase",
                "product": {
                    "relatedParty": [
                        {
                            "id": msisdn,
                            "name": "MSISDN",
                            "role": "Subscriber"
                        }
                    ],
                    "id": bundle_id,
                    "encProductId": enc_product_id
                }
            }
        ],
        "@type": "FlexRenew"
    }
    
    # هنستخدم نفس Headers بتاعة الموبايل بالظبط
    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'api-host': "ProductOrderingManagementHost",  # غيرناها عشان تتناسب مع التجديد
        'useCase': "FlexRenew",
        'Authorization': f"Bearer {token}",
        'api-version': "v2",
        'device-id': "b26ba335813fad21",
        'x-agent-operatingsystem': "15",
        'clientId': "AnaVodafoneAndroid",
        'x-agent-device': "Samsung SM-A165F",
        'x-agent-version': "2026.1.1",
        'x-agent-build': "1090",
        'msisdn': msisdn,
        'Content-Type': "application/json",
        'Accept-Language': "ar"
    }
    
    try:
        print("📤 إرسال طلب التجديد لخوادم الموبايل...")
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        print(f"📥 كود الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            print("✅✅ تم تجديد الباقة بنجاح!")
            try:
                result = response.json()
                print(f"الرد: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except:
                print(f"الرد: {response.text}")
            return True, "نجاح"
        elif response.status_code == 400:
            try:
                result = response.json()
                error_code = result.get('code')
                error_reason = result.get('reason')
                
                if error_code == "2255" and "Grace period" in error_reason:
                    print("❌❌ فشل التجديد: الرقم في فترة السماح (لا يوجد رصيد كافٍ)")
                    return False, "grace_period"
                else:
                    print(f"❌ فشل التجديد: {error_reason}")
                    print(f"كود الخطأ: {error_code}")
                    return False, "other_error"
            except:
                print(f"❌ الرد: {response.text}")
                return False, "unknown"
        else:
            print(f"❌ خطأ غير متوقع: {response.status_code}")
            print(f"الرد: {response.text}")
            return False, "unknown"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ فشل تجديد الباقة: {e}")
        return False, "exception"

def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("     برنامج تجديد باقات Flex - فودافون مصر")
    print("     (نسخة الموبايل الكاملة)")
    print("=" * 60)
    
    username = input("\n📱 أدخل رقم الهاتف (مثال: 01098786582): ").strip()
    password = input("🔑 أدخل كلمة المرور: ").strip()
    
    if not username or not password:
        print("❌ يجب إدخال رقم الهاتف وكلمة المرور")
        return
    
    # تجهيز الرقم
    if username.startswith('+2'):
        username = username[2:]
    elif username.startswith('2') and len(username) == 12:
        username = username[1:]
    
    print(f"\n📱 جاري معالجة الرقم: {username}")
    
    # 1. تسجيل الدخول
    token = login(username, password)
    if not token:
        return
    
    # 2. جلب المنتجات
    products = get_flex_products_mobile(username, token)
    if not products:
        print("❌ فشل جلب معلومات الباقات")
        return
    
    # 3. البحث عن الباقة الرئيسية
    selected_bundle = find_main_bundle_auto(products)
    if not selected_bundle:
        print("❌ لم يتم العثور على باقة رئيسية")
        return
    
    # 4. تجديد الباقة
    print("\n" + "=" * 60)
    print("🚀 جاري تجديد الباقة تلقائياً...")
    success, reason = renew_flex_bundle_mobile(username, token, selected_bundle)
    
    # 5. النتيجة النهائية
    print("\n" + "=" * 60)
    if success:
        print("🎉🎉 تم تجديد الباقة بنجاح! استمتع بخدماتك")
    else:
        if reason == "grace_period":
            print("😞 لم يتم تجديد الباقة - الرقم في فترة السماح")
            print("💡 نصيحة: تأكد من وجود رصيد كافٍ في حسابك")
        else:
            print("😞 لم يتم تجديد الباقة - يرجى المحاولة من التطبيق الرسمي")
    print("=" * 60)

if __name__ == "__main__":
    main()