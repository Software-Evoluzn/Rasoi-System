from flask import Flask, request, jsonify , render_template
import mysql.connector
from datetime import datetime, timedelta
from flask_cors import CORS

from werkzeug.security import generate_password_hash, check_password_hash

import qrcode
print("working")

app = Flask(__name__)
CORS(app)

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="rasoi_system"
)

cursor = db.cursor(dictionary=True)

#  --------------------------------------start  login ---------------------------------------------------

@app.route('/')
def home():
 return render_template('login.html')
    
@app.route('/login' ,methods=['POST'])
def login_customer():
    data = request.json
    
    email = data.get('email')
    password = data.get('password')
    
    
    try:
        
        query ="""
        
        SELECT * FROM customers
        WHERE email=%s 
        """
        
       
        
        cursor.execute(query,(email,))
        customer = cursor.fetchone()
        
        if customer:
            
            stored_password = customer['password']
            
            if check_password_hash(stored_password , password):
                 return jsonify({
                "message" : "Login Successfull"
                
                }),200
            
            else:
                  return jsonify({
                    "error": "Invalid Password"
                }), 401
                   
        else:
            
            return jsonify({
                  "error": "User Not Found"
            })
            
            
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500
        
    
#    -------------------------------------------login end ----------------------------------------------------

# ------------------------------------register start --------------------------------------------

@app.route('/register-page')
def register_page():

    return render_template('register.html')      
    
    


# Customer Registration API
@app.route('/register', methods=['POST'])
def register_customer():

    data = request.json

    name = data.get('name')
    mobile = data.get('mobile')
    email = data.get('email')
    password = data.get('password')
    
    hashed_password = generate_password_hash(password)
    

    try:
        query = """
        INSERT INTO customers(name, mobile, email,password)
        VALUES (%s, %s, %s , %s)
        """

        values = (name, mobile, email  ,hashed_password )

        cursor.execute(query, values)
        db.commit()

        return jsonify({
            "message": "Customer registered successfully"
        }), 201

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
        
        
# ------------------------------------------------------------register end-------------------------------------------

#  ----------------------------------------------------product linking  start ---------------------------------------




@app.route('/add-product', methods=['POST'])
def add_product():

    data = request.json

    product_id = data.get("product_id")
    product_name = data.get("product_name")
    serial_number = data.get("serial_number")
    qr_code = data.get("qr_code")
    warranty_years = data.get("warranty_years")
    created_at = data.get("created_at")

    query = """
    INSERT INTO products
    (
        product_id,
        product_name,
        serial_number,
        qr_code,
        warranty_years,
        created_at
    )
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        product_id,
        product_name,
        serial_number,
        qr_code,
        warranty_years,
        created_at
    )

    cursor.execute(query, values)
    db.commit()

    return jsonify({
        "message": "Product added successfully"
    })
    
    
@app.route('/product/<device_id>')
def product_page(device_id):

     query = """
     SELECT *
     FROM products
    WHERE device_id=%s
    """

     cursor.execute(query, (device_id,))

     product = cursor.fetchone()

     if not product:
        return jsonify({
            "error": "Invalid Product"
        }), 404

     return f"""

    <h2>Product Found</h2>

    <p>Device ID: {device_id}</p>

    <button onclick="registerProduct()">
        Register Product
    </button>

    <script>

    async function registerProduct() {{

        const response = await fetch(
            "http://192.168.1.53:5000/register-product",
            {{

                method: "POST",

                headers: {{
                    "Content-Type": "application/json"
                }},

                body: JSON.stringify({{

                    device_id: "{device_id}",
                    customer_name: "Sejal",
                    customer_mobile: "9876543210",
                    purchase_date: "2026-05-19"

                }})

            }}
        )

        const data = await response.json()
        console.log(data);

        alert(JSON.stringify(data))

    }}

    </script>

    """
     
     
 #  Qr-code forming and product linking;
@app.route('/register-product', methods=['POST'])
def register_product():

    try:
         
        data = request.get_json()
        
        device_id = data.get("device_id")
        customer_name = data.get("customer_name")
        customer_mobile = data.get("customer_mobile")
        purchase_date = data.get("purchase_date")

        # FIND PRODUCT
        query = """
        SELECT product_id, warranty_years, isRegistered
        FROM products
        WHERE device_id=%s
        """

        cursor.execute(query, (device_id,))

        product = cursor.fetchone()

        if not product:
            return jsonify({
                "error": "Product not found"
            }), 404

        # CHECK ALREADY REGISTERED
        if product["isRegistered"]:
            return jsonify({
                "error": "Product already registered"
            }), 400

        # WARRANTY
        purchase_date_obj = datetime.strptime(
            purchase_date,
            "%Y-%m-%d"
        )

        warranty_expiry = (
            purchase_date_obj +
            timedelta(days=365 * product["warranty_years"])
        )

        # STORE CUSTOMER LINKING
        insert_query = """
        INSERT INTO product_registrations
        (
            product_id,
            customer_name,
            customer_mobile,
            purchase_date,
            warranty_expiry
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            product["product_id"],
            customer_name,
            customer_mobile,
            purchase_date_obj.date(),
            warranty_expiry.date()
        )

        cursor.execute(insert_query, values)

        # MARK REGISTERED
        update_query = """
        UPDATE products
        SET isRegistered = TRUE
        WHERE product_id=%s
        """

        cursor.execute(
            update_query,
            (product["product_id"],)
        )

        db.commit()

        return jsonify({
            "message": "Product Linked Successfully",
            "device_id": device_id,
            "customer_name": customer_name,
            "warranty_expiry": str(warranty_expiry.date())
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500




# -----------------------------------------------------product linking  end ---------------------------------------

# -------------------------------
# SAVE OTP LOG
# -------------------------------
@app.route('/save-otp', methods=['POST'])
def save_otp():
    data = request.json

    mobile = data.get('mobile')
    otp = data.get('otp')

    cursor.execute("""
        INSERT INTO otp_logs (mobile, otp_code)
        VALUES (%s, %s)
    """, (mobile, otp))
    db.commit()

    return jsonify({
        "status": "success",
        "message": "OTP saved"
    })


# -------------------------------
# VERIFY OTP
# -------------------------------
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json

    mobile = data.get('mobile')
    otp = data.get('otp')

    cursor.execute("""
        SELECT * FROM otp_logs
        WHERE mobile=%s AND otp_code=%s
        ORDER BY otp_id DESC LIMIT 1
    """, (mobile, otp))

    result = cursor.fetchone()

    if result:
        cursor.execute("""
            UPDATE otp_logs SET verified=1
            WHERE otp_id=%s
        """, (result['otp_id'],))
        db.commit()

        return jsonify({
            "status": "success",
            "message": "OTP verified"
        })

    return jsonify({
        "status": "error",
        "message": "Invalid OTP"
    }), 400


# -------------------------------
# WARRANTY CHECK
# -------------------------------
@app.route('/warranty/<serial_number>', methods=['GET'])
def check_warranty(serial_number):
    cursor.execute("""
        SELECT rp.serial_number, rp.product_name,
               wr.warranty_start, wr.warranty_end, wr.status
        FROM registered_products rp
        JOIN warranty_records wr
        ON rp.registration_id = wr.registration_id
        WHERE rp.serial_number=%s
    """, (serial_number,))

    result = cursor.fetchone()

    if result:
        return jsonify(result)

    return jsonify({
        "status": "error",
        "message": "No warranty found"
    }), 404


# -------------------------------
# CREATE SERVICE TICKET
# -------------------------------
@app.route('/create-ticket', methods=['POST'])
def create_ticket():
    data = request.json

    serial_number = data.get('serial_number')
    issue = data.get('issue_description')

    cursor.execute("""
        SELECT registration_id FROM registered_products
        WHERE serial_number=%s
    """, (serial_number,))
    product = cursor.fetchone()

    if not product:
        return jsonify({
            "status": "error",
            "message": "Product not found"
        }), 404

    registration_id = product['registration_id']

    cursor.execute("""
        INSERT INTO service_tickets
        (registration_id, issue_description)
        VALUES (%s, %s)
    """, (registration_id, issue))
    db.commit()

    return jsonify({
        "status": "success",
        "message": "Service ticket created"
    })


# -------------------------------
# MAIN
# -------------------------------
if __name__ == '__main__':
    app.run( host="0.0.0.0",
    port=5000,
    debug=True)