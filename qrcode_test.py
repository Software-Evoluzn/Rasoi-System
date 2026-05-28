import qrcode
import os
import mysql.connector

# DATABASE CONNECTION
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="rasoi_system1"
)

cursor = db.cursor()

# QUERY
query = """
SELECT device_id
FROM products
"""

cursor.execute(query)

products = cursor.fetchall()

# CREATE FOLDER
os.makedirs("qrcodes", exist_ok=True)

# GENERATE QR
for product in products:

    device_id = product[0]

    img = qrcode.make(device_id)

    img.save(f"qrcodes/{device_id}.png")

    print(f"QR Generated for {device_id}")

print("All QR Codes Generated")