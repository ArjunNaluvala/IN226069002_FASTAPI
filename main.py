from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

# PRODUCTS DATABASE


products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

# CART + ORDERS STORAGE


cart = []
orders = []


# MODELS


class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)


# HELPER FUNCTIONS


def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None

def find_cart_item(product_id: int):
    for item in cart:
        if item["product_id"] == product_id:
            return item
    return None

# PRODUCTS ENDPOINTS


@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# CART ENDPOINTS


@app.post("/cart/add")
def add_to_cart(
    product_id: int = Query(...),
    quantity: int = Query(1, gt=0)
):

    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    existing = find_cart_item(product_id)

    if existing:
        existing["quantity"] += quantity
        existing["subtotal"] = existing["quantity"] * existing["unit_price"]

        return {
            "message": "Cart updated",
            "cart_item": existing
        }

    item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": product["price"] * quantity
    }

    cart.append(item)

    return {
        "message": "Added to cart",
        "cart_item": item
    }

# VIEW CART


@app.get("/cart")
def view_cart():

    if not cart:
        return {"message": "Cart is empty"}

    total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": total
    }

# REMOVE FROM CART


@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):

    item = find_cart_item(product_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    cart.remove(item)

    return {"message": f"{item['product_name']} removed from cart"}


# CHECKOUT


@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):

    if not cart:
        raise HTTPException(status_code=400, detail="CART_EMPTY")

    grand_total = 0
    placed_orders = []

    for item in cart:
        order = {
            "order_id": len(orders) + 1,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "subtotal": item["subtotal"],
            "delivery_address": data.delivery_address
        }

        orders.append(order)
        placed_orders.append(order)
        grand_total += item["subtotal"]

    cart.clear()

    return {
        "message": "Checkout successful",
        "orders_placed": len(placed_orders),
        "grand_total": grand_total,
        "orders": placed_orders
    }

# VIEW ORDERS

@app.get("/orders")
def get_orders():
    return {
        "orders": orders,
        "total_orders": len(orders)
    }