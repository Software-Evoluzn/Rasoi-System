from flask import Flask, request, jsonify, render_template
import mysql.connector
from datetime import datetime, timedelta
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print("working")

app = Flask(__name__)
CORS(app)

# -------------------------------
# GMAIL CONFIGURATION
# Yahan apna Gmail aur App Password daalo
# -------------------------------
GMAIL_USER     = "evoluzn999@gmail.com"       
GMAIL_PASSWORD = "euhf nozx wsjy pwbr"         
                                               

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="rasoi_system1"
)
cursor = db.cursor(dictionary=True)


# ---------------------------------------------------------------
# DB RECONNECT HELPER  (long idle time pe connection drop hota hai)
# ---------------------------------------------------------------
def get_cursor():
    global db, cursor
    try:
        db.ping(reconnect=True, attempts=3, delay=2)
    except Exception:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="rasoi_system1"
        )
    cursor = db.cursor(dictionary=True)
    return cursor


# -------------------------------
# CREATE TABLES
# -------------------------------
cur = get_cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100),
    mobile      VARCHAR(15),
    email       VARCHAR(100) UNIQUE,
    password    VARCHAR(255),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_id     INT PRIMARY KEY AUTO_INCREMENT,
    product_name   VARCHAR(100),
    serial_number  VARCHAR(100),
    qr_code        VARCHAR(100),
    warranty_years INT,
    created_at     DATETIME,
    device_id      VARCHAR(100),
    isRegistered   BOOLEAN DEFAULT FALSE
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS product_registrations (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    product_id      INT,
    customer_name   VARCHAR(100),
    customer_mobile VARCHAR(15),
    purchase_date   DATE,
    warranty_expiry DATE,
    create_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ✅ NEW TABLE — Email OTP store karne ke liye
cur.execute("""
CREATE TABLE IF NOT EXISTS password_reset_otps (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    email      VARCHAR(100) NOT NULL,
    otp        VARCHAR(6)   NOT NULL,
    expires_at DATETIME     NOT NULL,
    is_used    BOOLEAN      DEFAULT FALSE,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
)
""")


#Grains table
cur.execute("""
CREATE TABLE IF NOT EXISTS grains (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    value_name VARCHAR(100),
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()

print("Here Sejal !!!!!")

# -------------------------------
# INSERT DEFAULT GRAINS
# ------------------------------

cur.execute("SELECT COUNT(*) as total FROM grains")
count = cur.fetchone()

if count["total"] == 0:

    grains_data = [
        ("WHEAT", "wheat", "../static/img/wheat.png"),
        ("CHANA DAL", "chana_dal", "../static/img/chana_dal.png"),
        ("RICE", "rice", "../static/img/rice.png"),
        ("RAGI", "ragi", "../static/img/ragi.png"),
        ("JOWAR", "jowar", "../static/img/jowar.png"),
        ("BAJRA", "bajra", "../static/img/bajra.png"),
        ("MASALA", "masala", "../static/img/masala.png")
    ]

    cur.executemany("""
        INSERT INTO grains(name, value_name, image)
        VALUES (%s, %s, %s)
    """, grains_data)

    db.commit()

    print("✅ Default grains inserted")



# ---------------------------------------------------------------
# HELPER — Gmail se OTP email bhejna
# ---------------------------------------------------------------
def send_otp_email(to_email, otp):
    """
     Customer ke email par OTP bhejta hai.
     Returns True if email was sent successfully, False on error.
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Password Reset OTP - EVOLUZN INDIA"
        msg["From"]    = GMAIL_USER
        msg["To"]      = to_email

        # Plain text version
        text_body = f"""
Hello,

Your Password Reset OTP is:

    {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.

- Evoluzn Team
        """

        # HTML version (nice looking)
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 480px; margin: 40px auto; background: #fff;
                  border-radius: 12px; overflow: hidden;
                  box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
    .header {{ background: linear-gradient(135deg, #0f3460, #533483);
               padding: 28px 24px; text-align: center; }}
    .header h2 {{ color: #fff; margin: 0; font-size: 22px; letter-spacing: 1px; }}
    .body {{ padding: 32px 24px; text-align: center; }}
    .body p {{ color: #555; font-size: 15px; margin-bottom: 20px; }}
    .otp-box {{ display: inline-block; background: #f0ecff;
                border: 2px dashed #533483; border-radius: 10px;
                padding: 16px 40px; font-size: 36px; font-weight: 700;
                color: #533483; letter-spacing: 10px; margin-bottom: 20px; }}
    .note {{ font-size: 13px; color: #999; }}
    .footer {{ background: #f9f9f9; padding: 16px; text-align: center;
               font-size: 12px; color: #bbb; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>&#9889; EVOLUZN INDIA</h2>
    </div>
    <div class="body">
      <p>Your <strong>Password Reset OTP</strong> is below:</p>
      <div class="otp-box">{otp}</div>
      <p class="note">&#128338; This OTP is valid for <strong>10 minutes</strong>.<br>
         If you did not request this, please ignore this email.</p>
    </div>
    <div class="footer">Powered by EVOLUZN &nbsp;|&nbsp; Evoluzn Smart Home</div>
  </div>
</body>
</html>
        """

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())

        return True

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


# ===============================================================
#  FORGOT PASSWORD — STEP 1
#  Email check karo + OTP generate karo + Gmail se bhejo
# ===============================================================
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data  = request.json
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    cur = get_cursor()

    # 1. Check karo customer exist karta hai ya nahi
    cur.execute("SELECT customer_id, name FROM customers WHERE email = %s", (email,))
    customer = cur.fetchone()

    if not customer:
        # Return same message for security (prevents email enumeration)
        return jsonify({"error": "No account was found with this email."}), 404

    # 2. 6-digit OTP banao
    otp        = str(random.randint(100000, 999999))
    expires_at = datetime.now() + timedelta(minutes=10)

    # 3. Pehle ke unused OTPs expire karo (same email ke)
    cur.execute("""
        UPDATE password_reset_otps
        SET is_used = TRUE
        WHERE email = %s AND is_used = FALSE
    """, (email,))

    # 4. Naya OTP DB mein save karo
    cur.execute("""
        INSERT INTO password_reset_otps (email, otp, expires_at)
        VALUES (%s, %s, %s)
    """, (email, otp, expires_at))
    db.commit()

    # 5. Gmail se OTP bhejo
    sent = send_otp_email(email, otp)

    if not sent:
        return jsonify({"error": "There was a problem sending the email. Please try again."}), 500

    return jsonify({
        "message": f"OTP has been sent to '{email}'",
        "email"  : email
    }), 200


# ===============================================================
#  FORGOT PASSWORD — STEP 2
#  OTP verify karo
# ===============================================================
@app.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    data  = request.json
    email = data.get('email', '').strip().lower()
    otp   = data.get('otp', '').strip()

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required."}), 400

    cur = get_cursor()

    # Latest unused + unexpired OTP dhundo
    cur.execute("""
        SELECT id, expires_at
        FROM password_reset_otps
        WHERE email    = %s
          AND otp      = %s
          AND is_used  = FALSE
          AND expires_at > NOW()
        ORDER BY id DESC
        LIMIT 1
    """, (email, otp))

    record = cur.fetchone()

    if not record:
        return jsonify({"error": "OTP is incorrect or has expired. Please request a new one."}), 400

    # OTP sahi hai — mark as used (password reset ke baad use na ho)
    # Note: hum abhi mark nahi kar rahe — password reset pe mark karenge
    # Taaki user galti se page refresh kare to fir se enter kar sake

    return jsonify({
        "message": "OTP verified! Now set a new password.",
        "email"  : email
    }), 200


# ===============================================================
#  FORGOT PASSWORD — STEP 3
#  Naya password set karo + DB mein save karo
# ===============================================================
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data         = request.json
    email        = data.get('email', '').strip().lower()
    otp          = data.get('otp', '').strip()
    new_password = data.get('new_password', '').strip()

    if not email or not otp or not new_password:
        return jsonify({"error": "Email, OTP and new password are required."}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    cur = get_cursor()

    # OTP dobara verify karo (security ke liye)
    cur.execute("""
        SELECT id
        FROM password_reset_otps
        WHERE email    = %s
          AND otp      = %s
          AND is_used  = FALSE
          AND expires_at > NOW()
        ORDER BY id DESC
        LIMIT 1
    """, (email, otp))

    record = cur.fetchone()

    if not record:
        return jsonify({"error": "OTP is incorrect or has expired. Please request a new one."}), 400

    # Naya password hash karo
    hashed_pw = generate_password_hash(new_password)

    # Customers table mein update karo
    cur.execute("""
        UPDATE customers
        SET password = %s
        WHERE email  = %s
    """, (hashed_pw, email))

    # OTP ko used mark karo (dobara use na ho)
    cur.execute("""
        UPDATE password_reset_otps
        SET is_used = TRUE
        WHERE id = %s
    """, (record['id'],))

    db.commit()

    return jsonify({
        "message": "Password successfully reset! You can now login."
    }), 200


# ===============================================================
#  RESEND OTP — Same email pe naya OTP bhejo
# ===============================================================
@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    data  = request.json
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    cur = get_cursor()

    # Check karo customer exist karta hai
    cur.execute("SELECT customer_id FROM customers WHERE email = %s", (email,))
    customer = cur.fetchone()

    if not customer:
        return jsonify({"error": "No account was found with this email."}), 404

    # Rate limiting — last 1 minute mein OTP bheja tha?
    cur.execute("""
        SELECT created_at
        FROM password_reset_otps
        WHERE email = %s
          AND is_used = FALSE
        ORDER BY id DESC
        LIMIT 1
    """, (email,))
    last = cur.fetchone()

    if last:
        diff = (datetime.now() - last['created_at']).total_seconds()
        if diff < 60:
            wait = int(60 - diff)
            return jsonify({
                "error": f"Please try again after {wait} seconds."
            }), 429

    # Purane OTPs expire karo
    cur.execute("""
        UPDATE password_reset_otps
        SET is_used = TRUE
        WHERE email = %s AND is_used = FALSE
    """, (email,))

    # Naya OTP
    otp        = str(random.randint(100000, 999999))
    expires_at = datetime.now() + timedelta(minutes=10)

    cur.execute("""
        INSERT INTO password_reset_otps (email, otp, expires_at)
        VALUES (%s, %s, %s)
    """, (email, otp, expires_at))
    db.commit()

    sent = send_otp_email(email, otp)

    if not sent:
        return jsonify({"error": "There was a problem sending the email."}), 500

    return jsonify({"message": "A new OTP has been sent to your email."}), 200


# ==============================================================
#  BAAKI SAARE PURANE ROUTES (unchanged)
# ==============================================================

@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_customer():
    data     = request.json
    email    = data.get('email')
    password = data.get('password')

    try:
        cur = get_cursor()
        cur.execute("SELECT * FROM customers WHERE email=%s", (email,))
        customer = cur.fetchone()

        if customer:
            if check_password_hash(customer['password'], password):
                return jsonify({
                    "message": "Login Successfull",
                    "name"   : customer['name'],      # ✅ add
                    "mobile" : customer['mobile'],    # ✅ add
                    "email"  : customer['email']      # ✅ add
                }), 200
            else:
                return jsonify({"error": "Invalid Password"}), 401
        else:
            return jsonify({"error": "User Not Found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/register-page')
def register_page():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_customer():
    data     = request.json
    name     = data.get('name')
    mobile   = data.get('mobile')
    email    = data.get('email')
    password = data.get('password')

    hashed_password = generate_password_hash(password)

    try:
        cur = get_cursor()
        cur.execute("""
            INSERT INTO customers(name, mobile, email, password)
            VALUES (%s, %s, %s, %s)
        """, (name, mobile, email, hashed_password))
        db.commit()
        return jsonify({"message": "Customer registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# scannn
@app.route('/product_scan')
def product_link():
    return render_template('scanner.html')




@app.route('/add-product', methods=['POST'])
def add_product():
    data          = request.json
    product_id    = data.get("product_id")
    product_name  = data.get("product_name")
    serial_number = data.get("serial_number")
    qr_code       = data.get("qr_code")
    warranty_years= data.get("warranty_years")
    created_at    = data.get("created_at")

    cur = get_cursor()
    cur.execute("""
        INSERT INTO products
        (product_id, product_name, serial_number, qr_code, warranty_years, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (product_id, product_name, serial_number, qr_code, warranty_years, created_at))
    db.commit()
    return jsonify({"message": "Product added successfully"})


@app.route('/product/<device_id>') 
def product_page(device_id):
    cur = get_cursor()
    cur.execute("SELECT * FROM products WHERE device_id=%s", (device_id,))
    product = cur.fetchone()
 
    if not product:
        return jsonify({"error": "Invalid Product"}), 404
 
    # Return JSON so scanner.js can display the details
    return jsonify({
        "product_id"    : product["product_id"],
        "product_name"  : product["product_name"],
        "serial_number" : product["serial_number"],
        "device_id"     : product["device_id"],
        "warranty_years": product["warranty_years"],
        "isRegistered"  : product["isRegistered"],
        # mac_id / model_number — add these columns to your products
        # table if you need them; for now we send what we have
        "model_number"  : product.get("model_number", "N/A"),
        "mac_id"        : product.get("mac_id", "N/A"),
    })
 

# @app.route('/register-product', methods=['POST'])
# def register_product():
#     try:
#         data            = request.get_json()
#         device_id       = data.get("device_id")
#         customer_name   = data.get("customer_name", "").strip()
#         customer_mobile = data.get("customer_mobile", "").strip()
#         purchase_date   = data.get("purchase_date")

#         # ✅ Validation — naam required hai
#         if not customer_name:
#             return jsonify({"error": "Customer name is required"}), 400

#         cur = get_cursor()

#         # Product fetch karo
#         cur.execute("""
#             SELECT product_id, product_name, serial_number,
#                    warranty_years, isRegistered,
#                    COALESCE(model_number, 'N/A') AS model_number,
#                    COALESCE(mac_id, 'N/A')        AS mac_id
#             FROM products WHERE device_id = %s
#         """, (device_id,))
#         product = cur.fetchone()

#         if not product:
#             return jsonify({"error": "Product not found"}), 404

#         # ✅ CHECK 1 — Product already registered hai kisi ke naam pe?
#         if product["isRegistered"]:
#             # Dekho kisne register kiya tha
#             cur.execute("""
#                 SELECT customer_name, customer_mobile
#                 FROM product_registrations
#                 WHERE product_id = %s
#                 ORDER BY id DESC LIMIT 1
#             """, (product["product_id"],))
#             existing = cur.fetchone()

#             owner = existing["customer_name"] if existing and existing["customer_name"] else "someone else"
#             return jsonify({
#                 "error": f"This product is already registered under '{owner}'. Only the original owner can register this product."
#             }), 400

#         purchase_date_obj = datetime.strptime(purchase_date, "%Y-%m-%d")
#         warranty_expiry   = purchase_date_obj + timedelta(days=365 * product["warranty_years"])

#         cur.execute("""
#             INSERT INTO product_registrations
#             (product_id, customer_name, customer_mobile, purchase_date, warranty_expiry)
#             VALUES (%s, %s, %s, %s, %s)
#         """, (
#             product["product_id"],
#             customer_name,
#             customer_mobile,
#             purchase_date_obj.date(),
#             warranty_expiry.date()
#         ))

#         cur.execute("""
#             UPDATE products SET isRegistered = TRUE WHERE product_id = %s
#         """, (product["product_id"],))

#         db.commit()

#         print(f"[REGISTER] ✅ Product '{product['serial_number']}' registered under '{customer_name}'")

#         return jsonify({
#             "message"        : "Product Linked Successfully",
#             "device_id"      : device_id,
#             "product_name"   : product["product_name"],
#             "serial_number"  : product["serial_number"],
#             "model_number"   : product["model_number"],
#             "mac_id"         : product["mac_id"],
#             "customer_name"  : customer_name,
#             "customer_mobile": customer_mobile,
#             "purchase_date"  : str(purchase_date_obj.date()),
#             "warranty_expiry": str(warranty_expiry.date()),
#             "warranty_years" : product["warranty_years"],
#         })

#     except Exception as e:
#         print(f"[REGISTER] 💥 ERROR: {e}")
#         return jsonify({"error": str(e)}), 500


@app.route('/register-product', methods=['POST'])
def register_product():
    try:
        data            = request.get_json()
        device_id       = data.get("device_id")
        customer_name   = data.get("customer_name", "").strip()
        customer_mobile = data.get("customer_mobile", "").strip()
        purchase_date   = data.get("purchase_date")

        # ✅ Validation — naam required hai
        if not customer_name:
            return jsonify({"error": "Customer name is required"}), 400

        cur = get_cursor()

        # Product fetch karo
        cur.execute("""
            SELECT product_id, product_name, serial_number,
                   warranty_years, isRegistered,
                   COALESCE(model_number, 'N/A') AS model_number,
                   COALESCE(mac_id, 'N/A')        AS mac_id
            FROM products WHERE device_id = %s
        """, (device_id,))
        product = cur.fetchone()

        if not product:
            return jsonify({"error": "Product not found"}), 404

        # ✅ CHECK 1 — Product already registered hai kisi ke naam pe?
        if product["isRegistered"]:
            # Dekho kisne register kiya tha
            cur.execute("""
                SELECT customer_name, customer_mobile
                FROM product_registrations
                WHERE product_id = %s
                ORDER BY id DESC LIMIT 1
            """, (product["product_id"],))
            existing = cur.fetchone()

            owner = existing["customer_name"] if existing and existing["customer_name"] else "someone else"
            return jsonify({
                "error": f"This product is already registered under '{owner}'. Only the original owner can register this product."
            }), 400

        purchase_date_obj = datetime.strptime(purchase_date, "%Y-%m-%d")
        warranty_expiry   = purchase_date_obj + timedelta(days=365 * product["warranty_years"])

        cur.execute("""
            INSERT INTO product_registrations
            (product_id, customer_name, customer_mobile, purchase_date, warranty_expiry)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            product["product_id"],
            customer_name,
            customer_mobile,
            purchase_date_obj.date(),
            warranty_expiry.date()
        ))

        cur.execute("""
            UPDATE products SET isRegistered = TRUE WHERE product_id = %s
        """, (product["product_id"],))

        db.commit()

        print(f"[REGISTER] ✅ Product '{product['serial_number']}' registered under '{customer_name}'")

        return jsonify({
            "message"        : "Product Linked Successfully",
            "device_id"      : device_id,
            "product_name"   : product["product_name"],
            "serial_number"  : product["serial_number"],
            "model_number"   : product["model_number"],
            "mac_id"         : product["mac_id"],
            "customer_name"  : customer_name,
            "customer_mobile": customer_mobile,
            "purchase_date"  : str(purchase_date_obj.date()),
            "warranty_expiry": str(warranty_expiry.date()),
            "warranty_years" : product["warranty_years"],
        })

    except Exception as e:
        print(f"[REGISTER] 💥 ERROR: {e}")
        return jsonify({"error": str(e)}), 500


# yeh code correct likh prodcut warrnt show karna hain sath yeh prduct kisss user ne leya hain oske information babar apne ko bckend se fetch karke fronte pe bhjne hain tabbhi apan fronted pe show kar payenge 
@app.route('/warranty-page')
def warranty_page():
    return render_template('warranty.html')

# Replace your existing /warranty/<serial_number> route with this:
@app.route('/warranty/<serial_number>', methods=['GET'])
def check_warranty(serial_number):
    try:
        cur = get_cursor()

        print(f"\n{'='*50}")
        print(f"[WARRANTY] Request aaya serial: '{serial_number}'")
        print(f"{'='*50}")

        cur.execute("""
            SELECT
                p.product_name,
                p.serial_number,
                COALESCE(p.model_number, 'N/A') AS model_number,
                COALESCE(p.mac_id,       'N/A') AS mac_id,
                pr.customer_name,
                pr.customer_mobile,
                pr.purchase_date,
                pr.warranty_expiry
            FROM products p
            JOIN product_registrations pr
              ON p.product_id = pr.product_id
            WHERE p.serial_number = %s
            ORDER BY pr.id DESC
            LIMIT 1
        """, (serial_number,))

        result = cur.fetchone()

        print(f"[WARRANTY] DB se raw result: {result}")  # 👈 DB ka raw data

        if not result:
            print(f"[WARRANTY] ❌ Koi record nahi mila serial '{serial_number}' ke liye")
            return jsonify({
                "status" : "error",
                "message": "No warranty found for this serial number"
            }), 404

        result["purchase_date"]   = str(result["purchase_date"])
        result["warranty_expiry"] = str(result["warranty_expiry"])

        from datetime import date
        today            = date.today()
        expiry           = date.fromisoformat(result["warranty_expiry"])
        result["status"] = "active" if expiry >= today else "expired"

        print(f"[WARRANTY] ✅ Final JSON jo frontend ko bhej raha hain:")
        for key, val in result.items():
            print(f"           {key:20s} = {val}")
        print(f"{'='*50}\n")

        return jsonify(result), 200

    except Exception as e:
        print(f"[WARRANTY] 💥 ERROR: {e}")
        return jsonify({"error": str(e)}), 500
    
# ------------------------------------------------Dashboard Page ----------------------------------------------------------
    
@app.route('/dashboard_page')
def dashboard_link():
    return render_template('dashboard.html')

# -------------------------------------------------------------------------------------------------------------------------



# ---------------------------------------------Multiple grain ------------------------------------------------------------
@app.route('/multiple_grain_page')
def multiple_grain_link():
    return render_template('multiple_grains.html')



# --------------------------------------------- GRAIN API --------------------------------------------

@app.route('/api/grains', methods=['GET'])
def get_grains():

    try:

        cur = get_cursor()

        cur.execute("""
            SELECT
                id,
                name,
                value_name,
                image
            FROM grains
        """)

        grains = cur.fetchall()

        return jsonify(grains), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# ----------------------------------------------------------------------------------------------------
    
    



# -----------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------Single grain ---------------------------------------------------------

@app.route('/single_grain_page')
def single_grain_link():
    return render_template('single_grain.html')

# ----------------------------------------------------------------------------------------------------------------------



    
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)