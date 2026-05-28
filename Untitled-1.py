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
