def create_customer(cursor,customer):
    cursor.execute(
        "INSERT INTO customers (full_name, email, phone,address)"
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (
            customer.full_name,
            customer.email,
            customer.phone,
            customer.address,

        )
    )
    return cursor.fetchone()[0]
