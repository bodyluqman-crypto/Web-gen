# app.py - Dragon Generator Store
# متوافق مع Vercel - نظام دفع عبر ID Free Fire

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import json
import os
import time
import random
import requests
import hmac
import hashlib
import base64
import threading
import re
from datetime import datetime

app = Flask(__name__)

# ======================== إعدادات الدفع ========================
PAYMENT_ID = "2129828082"  # ID Free Fire للدفع
PRICE_PER_ACCOUNT = 0.50   # سعر الحساب بالدولار

# ======================== إعدادات التوليد ========================
class Config:
    HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
    API_KEY = bytes.fromhex(HEX_KEY)
    REGISTER_URL = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
    TOKEN_URL = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    MAJOR_REGISTER_URL = "https://loginbp.ggpolarbear.com/MajorRegister"
    MAJOR_LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"
    
    REGION_LANG = {
        "ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", "TH": "th",
        "BD": "bn", "PK": "ur", "TW": "zh", "CIS": "ru", "SAC": "es", "BR": "pt"
    }

# ======================== قاعدة بيانات مؤقتة (JSON) ========================
ORDERS_FILE = "orders.json"

def load_orders():
    try:
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_orders(orders):
    try:
        with open(ORDERS_FILE, 'w') as f:
            json.dump(orders, f, indent=2)
    except:
        pass

# ======================== دوال التوليد ========================
def generate_random_name(prefix):
    digits = '0123456789'
    suffix = ''.join(random.choices(digits, k=6))
    return f"{prefix}{suffix}"

def generate_custom_password():
    return ''.join(random.choice('0123456789ABCDEF') for _ in range(64))

def generate_account(region, name_prefix):
    try:
        password = generate_custom_password()
        name = generate_random_name(name_prefix)
        
        payload_register = json.dumps(
            {"app_id": 100067, "client_type": 2, "password": password, "source": 2},
            separators=(',', ':')
        )
        signature = hmac.new(Config.API_KEY, payload_register.encode(), hashlib.sha256).hexdigest()
        
        headers_reg = {
            "User-Agent": "GarenaMSDK/4.0.39(SM-A325M ;Android 13;en;HK;)",
            "Authorization": f"Signature {signature}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "Connection": "Keep-Alive",
            "Host": "100067.connect.garena.com",
        }
        
        resp_reg = requests.post(
            Config.REGISTER_URL,
            headers=headers_reg,
            data=payload_register,
            timeout=20,
            verify=False
        )
        
        if resp_reg.status_code != 200:
            return None
            
        reg_json = resp_reg.json()
        if reg_json.get("code") != 0:
            return None
            
        uid = reg_json['data']['uid']
        
        payload_token = json.dumps({
            "client_id": 100067,
            "client_secret": Config.HEX_KEY,
            "client_type": 2,
            "password": password,
            "response_type": "token",
            "uid": uid,
        }, separators=(',', ':'))
        
        signature2 = hmac.new(Config.API_KEY, payload_token.encode(), hashlib.sha256).hexdigest()
        
        headers_tok = {
            "User-Agent": "GarenaMSDK/4.0.39(SM-A325M ;Android 13;en;HK;)",
            "Authorization": f"Signature {signature2}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "Connection": "Keep-Alive",
            "Host": "100067.connect.garena.com",
        }
        
        resp_tok = requests.post(
            Config.TOKEN_URL,
            headers=headers_tok,
            data=payload_token,
            timeout=20,
            verify=False
        )
        
        if resp_tok.status_code != 200:
            return None
            
        tok_json = resp_tok.json()
        if tok_json.get("code") != 0:
            return None
            
        return {
            "uid": uid,
            "password": password,
            "name": name,
            "region": region,
            "level": "2"
        }
        
    except Exception as e:
        return None

def generate_accounts(region, name_prefix, count):
    accounts = []
    for i in range(count):
        account = generate_account(region, name_prefix)
        if account:
            accounts.append(account)
        time.sleep(0.5)
    return accounts

# ======================== HTML Template ========================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐉 DRAGON Store - شراء حسابات Free Fire</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #fff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 550px;
            width: 100%;
            background: #121212;
            border-radius: 20px;
            padding: 35px 30px;
            border: 1px solid #2a2a2a;
            box-shadow: 0 25px 80px rgba(0,0,0,0.9);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #ff4444, #ff8800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p {
            color: #888;
            font-size: 14px;
            margin-top: 5px;
        }
        .payment-id-box {
            background: #1a1a1a;
            border: 2px dashed #ff4444;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 25px;
        }
        .payment-id-box .label {
            color: #888;
            font-size: 13px;
        }
        .payment-id-box .id {
            font-size: 28px;
            font-weight: bold;
            color: #ff4444;
            margin: 5px 0;
            letter-spacing: 2px;
        }
        .payment-id-box .note {
            color: #666;
            font-size: 12px;
        }
        .form-group {
            margin-bottom: 18px;
        }
        .form-group label {
            display: block;
            color: #aaa;
            font-size: 13px;
            margin-bottom: 5px;
            font-weight: 600;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px 16px;
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 10px;
            color: #fff;
            font-size: 15px;
            transition: border 0.3s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #ff4444;
        }
        .form-group select option { background: #1a1a1a; }
        .price-box {
            background: #1a1a1a;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
            border: 1px solid #2a2a2a;
        }
        .price-box .price {
            font-size: 28px;
            color: #00ff88;
            font-weight: bold;
        }
        .price-box .price span { font-size: 16px; color: #888; }
        .btn-buy {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #ff4444, #cc2222);
            color: #fff;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            letter-spacing: 1px;
        }
        .btn-buy:hover { transform: scale(1.02); opacity: 0.9; }
        .btn-buy:disabled { background: #444; cursor: not-allowed; transform: none; }
        .status-box {
            margin-top: 20px;
            padding: 20px;
            background: #1a1a1a;
            border-radius: 12px;
            display: none;
            border: 1px solid #2a2a2a;
            max-height: 400px;
            overflow-y: auto;
        }
        .status-box .success { color: #00ff88; }
        .status-box .pending { color: #ffaa00; }
        .status-box .error { color: #ff4444; }
        .accounts-list { margin-top: 15px; }
        .account-item {
            background: #0d0d0d;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            border: 1px solid #222;
            font-size: 13px;
        }
        .account-item .label { color: #666; font-weight: 600; }
        .account-item .value { color: #fff; }
        .loading { text-align: center; padding: 20px; }
        .spinner {
            display: inline-block;
            width: 35px;
            height: 35px;
            border: 3px solid #2a2a2a;
            border-top: 3px solid #ff4444;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .copy-btn {
            background: #2a2a2a;
            border: none;
            color: #aaa;
            padding: 4px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 8px;
        }
        .copy-btn:hover { background: #3a3a3a; color: #fff; }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #444;
            font-size: 12px;
        }
        .steps {
            margin: 15px 0;
            padding: 15px;
            background: #0d0d0d;
            border-radius: 10px;
        }
        .steps li {
            color: #aaa;
            font-size: 13px;
            margin: 5px 0;
            list-style: none;
        }
        .steps li::before { content: "▸ "; color: #ff4444; }
        @media (max-width: 480px) {
            .container { padding: 20px 15px; }
            .header h1 { font-size: 24px; }
            .payment-id-box .id { font-size: 22px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐉 DRAGON GEN</h1>
            <p>شراء حسابات Free Fire - تسليم تلقائي</p>
        </div>

        <div class="payment-id-box">
            <div class="label">📤 أرسل المبلغ إلى ID</div>
            <div class="id" id="paymentId">{{ payment_id }}</div>
            <button class="copy-btn" onclick="copyID()">📋 نسخ</button>
            <div class="note">* سعر الحساب الواحد: ${{ price_per_account }}</div>
        </div>

        <div class="steps">
            <li>أرسل المبلغ إلى ID: <strong>{{ payment_id }}</strong></li>
            <li>أدخل بياناتك واختر عدد الحسابات</li>
            <li>اضغط "شراء" وسيتم التسليم تلقائيًا</li>
        </div>

        <div class="form-group">
            <label>📧 بريدك الإلكتروني</label>
            <input type="email" id="email" placeholder="أدخل بريدك الإلكتروني">
        </div>

        <div class="form-group">
            <label>👤 اسم الحساب</label>
            <input type="text" id="accountName" placeholder="مثال: DRAGON" value="DRAGON">
        </div>

        <div class="form-group">
            <label>🌍 المنطقة</label>
            <select id="region">
                <option value="ME">الشرق الأوسط (ME)</option>
                <option value="IND">الهند (IND)</option>
                <option value="ID">إندونيسيا (ID)</option>
                <option value="VN">فيتنام (VN)</option>
                <option value="TH">تايلاند (TH)</option>
                <option value="BD">بنجلاديش (BD)</option>
                <option value="PK">باكستان (PK)</option>
                <option value="TW">تايوان (TW)</option>
                <option value="CIS">روسيا (CIS)</option>
                <option value="SAC">أمريكا الجنوبية (SAC)</option>
                <option value="BR">البرازيل (BR)</option>
            </select>
        </div>

        <div class="form-group">
            <label>🔢 عدد الحسابات</label>
            <input type="number" id="count" value="1" min="1" max="50">
        </div>

        <div class="price-box">
            <div class="price">$<span id="price">0.50</span></div>
            <div style="color:#666;font-size:13px;">سعر الحساب الواحد: ${{ price_per_account }}</div>
        </div>

        <button class="btn-buy" id="buyBtn">🛒 شراء الآن</button>

        <div class="status-box" id="statusBox">
            <div id="statusContent"></div>
        </div>

        <div class="footer">DRAGON GEN © 2024 - تسليم تلقائي بعد الدفع</div>
    </div>

    <script>
        let orderId = null;
        let checkInterval = null;

        function copyID() {
            const id = document.getElementById('paymentId').textContent;
            navigator.clipboard.writeText(id).then(() => {
                const btn = event.target;
                btn.textContent = '✅ تم النسخ';
                setTimeout(() => btn.textContent = '📋 نسخ', 2000);
            });
        }

        document.getElementById('count').addEventListener('input', function() {
            const count = parseInt(this.value) || 1;
            const price = (count * {{ price_per_account }}).toFixed(2);
            document.getElementById('price').textContent = price;
        });

        document.getElementById('buyBtn').addEventListener('click', async function() {
            const email = document.getElementById('email').value.trim();
            const accountName = document.getElementById('accountName').value.trim();
            const region = document.getElementById('region').value;
            const count = parseInt(document.getElementById('count').value) || 1;

            if (!email) { alert('الرجاء إدخال البريد الإلكتروني'); return; }
            if (!accountName) { alert('الرجاء إدخال اسم الحساب'); return; }

            this.disabled = true;
            this.textContent = '⏳ جاري المعالجة...';

            try {
                const response = await fetch('/api/create_order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, account_name: accountName, region, count })
                });

                const data = await response.json();

                if (data.success) {
                    orderId = data.order_id;
                    showStatus('pending', '⏳ جاري توليد الحسابات...');
                    if (checkInterval) clearInterval(checkInterval);
                    checkInterval = setInterval(checkOrderStatus, 3000);
                } else {
                    showStatus('error', '❌ حدث خطأ، حاول مرة أخرى');
                    this.disabled = false;
                    this.textContent = '🛒 شراء الآن';
                }
            } catch (error) {
                showStatus('error', '❌ خطأ في الاتصال');
                this.disabled = false;
                this.textContent = '🛒 شراء الآن';
            }
        });

        async function checkOrderStatus() {
            if (!orderId) return;
            try {
                const response = await fetch(`/api/check_order/${orderId}`);
                const data = await response.json();
                if (data.status === 'delivered') {
                    clearInterval(checkInterval);
                    showStatus('success', '✅ تم التسليم!', data.accounts);
                    document.getElementById('buyBtn').disabled = false;
                    document.getElementById('buyBtn').textContent = '🛒 شراء الآن';
                }
            } catch (error) { console.error(error); }
        }

        function showStatus(type, message, accounts = null) {
            const box = document.getElementById('statusBox');
            const content = document.getElementById('statusContent');
            box.style.display = 'block';
            
            if (type === 'success') {
                let html = `<div class="success">${message}</div>`;
                if (accounts && accounts.length > 0) {
                    html += `<div class="accounts-list">`;
                    accounts.forEach((acc, i) => {
                        html += `
                            <div class="account-item">
                                <div><span class="label">#${i+1}</span></div>
                                <div><span class="label">UID:</span> <span class="value">${acc.uid}</span></div>
                                <div><span class="label">Password:</span> <span class="value">${acc.password.substring(0, 16)}...</span></div>
                                <div><span class="label">Name:</span> <span class="value">${acc.name}</span></div>
                                <div><span class="label">Region:</span> <span class="value">${acc.region}</span></div>
                                <div><span class="label">Level:</span> <span class="value">${acc.level}</span></div>
                            </div>
                        `;
                    });
                    html += `</div>`;
                }
                content.innerHTML = html;
            } else if (type === 'pending') {
                content.innerHTML = `<div class="loading"><div class="spinner"></div><p style="margin-top:10px;">${message}</p></div>`;
            } else {
                content.innerHTML = `<div class="error">${message}</div>`;
            }
        }
    </script>
</body>
</html>
'''

# ======================== Routes ========================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                  payment_id=PAYMENT_ID, 
                                  price_per_account=PRICE_PER_ACCOUNT)

@app.route('/api/create_order', methods=['POST'])
def create_order():
    data = request.json
    email = data.get('email')
    account_name = data.get('account_name')
    region = data.get('region')
    count = data.get('count', 1)
    
    order_id = f"ORD-{int(time.time())}-{random.randint(1000, 9999)}"
    
    orders = load_orders()
    orders[order_id] = {
        'order_id': order_id,
        'email': email,
        'account_name': account_name,
        'region': region,
        'count': count,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    save_orders(orders)
    
    # توليد في الخلفية
    def generate():
        time.sleep(2)
        accounts = generate_accounts(region, account_name, count)
        orders = load_orders()
        if order_id in orders:
            orders[order_id]['status'] = 'delivered'
            orders[order_id]['accounts'] = accounts
            save_orders(orders)
    
    thread = threading.Thread(target=generate)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'order_id': order_id})

@app.route('/api/check_order/<order_id>')
def check_order(order_id):
    orders = load_orders()
    order = orders.get(order_id)
    
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'})
    
    if order.get('status') == 'delivered':
        return jsonify({
            'success': True,
            'status': 'delivered',
            'accounts': order.get('accounts', [])
        })
    
    return jsonify({'success': True, 'status': order.get('status', 'pending')})

# ======================== Vercel ========================
# هذا الجزء مهم عشان Vercel
app.debug = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)