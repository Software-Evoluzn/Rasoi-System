from flask import Flask, request, jsonify , render_template
import mysql.connector
from datetime import datetime, timedelta
from flask_cors import CORS

from flask import session

from werkzeug.security import generate_password_hash, check_password_hash

import qrcode
print("working")

app = Flask(__name__)
app.secret_key = "rasoi_secret_key"

CORS(app)

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
   
)

cursor = db.cursor(dictionary=True)

cursor.execute(
    "CREATE DATABASE IF NOT EXISTS rasoi_system1"
)

cursor.execute("USE rasoi_system1")

# Create tables 

cursor.execute("""

CREATE TABLE IF NOT EXISTS customers (

    customer_id INT PRIMARY KEY AUTO_INCREMENT,

    name VARCHAR(100),

    mobile VARCHAR(15),

    email VARCHAR(100) UNIQUE,

    password VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)

""")



cursor.execute("""

CREATE TABLE IF NOT EXISTS products (

      product_id INT PRIMARY KEY AUTO_INCREMENT,

    product_name VARCHAR(100),

    serial_number VARCHAR(100),

    model_number VARCHAR(100),

    mac_id VARCHAR(100),

    qr_code VARCHAR(100),

    warranty_years INT,

    created_at DATETIME,

    device_id VARCHAR(100),

    isRegistered BOOLEAN DEFAULT FALSE

)

""")



cursor.execute("""

CREATE TABLE IF NOT EXISTS product_registrations (

    id INT PRIMARY KEY AUTO_INCREMENT,

    product_id INT,

    customer_name VARCHAR(100),

    customer_mobile VARCHAR(15),

    purchase_date DATE,

    warranty_expiry DATE,

    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)

""")


db.commit()


# ----------------------------------create tables -------------------------------------------------




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
                 session["customer_id"] = customer["customer_id"]
                
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

@app.route('/product_scan')
def product_link():
    return render_template('scanner.html')



@app.route('/add-product', methods=['POST'])
def add_product():

    data = request.json

    product_name = data.get("product_name")

    serial_number = data.get("serial_number")

    model_number = data.get("model_number")

    mac_id = data.get("mac_id")

    qr_code = data.get("qr_code")

    warranty_years = data.get("warranty_years")

    created_at = data.get("created_at")

    device_id = data.get("device_id")

    isRegistered = data.get("isRegistered", False)

    query = """
    INSERT INTO products
    (
        product_name,
        serial_number,
        model_number,
        mac_id,
        qr_code,
        warranty_years,
        created_at,
        device_id,
        isRegistered
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        product_name,
        serial_number,
        model_number,
        mac_id,
        qr_code,
        warranty_years,
        created_at,
        device_id,
        isRegistered
    )

    cursor.execute(query, values)

    db.commit()

    return jsonify({
        "message": "Product added successfully"
    })
    
@app.route('/product/<device_id>')
def product_page(device_id):

     query = """
       SELECT
        serial_number,
        model_number,
        mac_id
    FROM products
    WHERE device_id=%s
    """

     cursor.execute(query, (device_id,))

     product = cursor.fetchone()

     if not product:
        return jsonify({
             "serial_number": "Not Found",

        "model_number": "Not Found",

        "mac_id": "Not Found"
        }), 404
        
     return jsonify({
        "serial_number": product["serial_number"],

        "model_number": product["model_number"],

        "mac_id": product["mac_id"]
    })

     
     
 #  Qr-code forming and product linking;
@app.route('/register-product', methods=['POST'])
def register_product():

    try:

        data = request.get_json()

        device_id = data.get("device_id")
        purchase_date = data.get("purchase_date")

        customer_id = session.get("customer_id")

        if not customer_id:

            return jsonify({
                "error": "User not logged in"
            }), 401

        # CUSTOMER DETAILS
        customer_query = """
        SELECT name, mobile
        FROM customers
        WHERE customer_id=%s
        """

        cursor.execute(customer_query, (customer_id,))

        customer = cursor.fetchone()

        customer_name = customer["name"]
        customer_mobile = customer["mobile"]

        # PRODUCT CHECK
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

        if product["isRegistered"]:

            return jsonify({
                "error": "Product already registered"
            }), 400

        purchase_date_obj = datetime.strptime(
            purchase_date,
            "%Y-%m-%d"
        )

        warranty_expiry = (
            purchase_date_obj +
            timedelta(days=365 * product["warranty_years"])
        )

        # INSERT REGISTRATION
        insert_query = """
        INSERT INTO product_registrations
        (
            product_id,
            customer_name,
            customer_mobile,
            purchase_date,
            warranty_expiry
        )
        VALUES (%s,%s,%s,%s,%s)
        """

        values = (
            product["product_id"],
            customer_name,
            customer_mobile,
            purchase_date_obj.date(),
            warranty_expiry.date()
        )

        cursor.execute(insert_query, values)

        # UPDATE PRODUCT
        update_query = """
        UPDATE products
        SET isRegistered=TRUE
        WHERE product_id=%s
        """

        cursor.execute(
            update_query,
            (product["product_id"],)
        )

        db.commit()

        return jsonify({

            "message": "Product Linked Successfully",

            "customer_name": customer_name,

            "warranty_expiry":
            str(warranty_expiry.date())

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500



# -----------------------------------------------------product linking  end ---------------------------------------


# -------------------------------
# MAIN
# -------------------------------
if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
    port=5000,
    
    debug=True
     )