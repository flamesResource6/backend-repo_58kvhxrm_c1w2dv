import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Ecommerce API Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Utility models
class ProductCreate(Product):
    pass

class OrderCreate(Order):
    pass

# Seed example products if collection is empty
@app.post("/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"inserted": 0, "message": "Products already exist"}

    demo = [
        {
            "title": "Classic Tee",
            "description": "100% cotton unisex t-shirt",
            "price": 24.99,
            "category": "Apparel",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1520975693419-6349b3baaacf?w=800",
            "rating": 4.6
        },
        {
            "title": "Leather Backpack",
            "description": "Minimal everyday carry backpack",
            "price": 129.00,
            "category": "Accessories",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=800",
            "rating": 4.7
        },
        {
            "title": "Ceramic Mug",
            "description": "12oz matte ceramic mug",
            "price": 16.50,
            "category": "Home",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=800",
            "rating": 4.8
        },
        {
            "title": "Noise-canceling Headphones",
            "description": "Over-ear wireless with ANC",
            "price": 199.99,
            "category": "Electronics",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1518449037766-8db0ae1f7da1?w=800",
            "rating": 4.4
        }
    ]
    inserted = 0
    for p in demo:
        create_document("product", p)
        inserted += 1
    return {"inserted": inserted}

# Products endpoints
@app.get("/products", response_model=List[Product])
def list_products(category: Optional[str] = None):
    filt = {"category": category} if category else {}
    docs = get_documents("product", filt)
    # Convert Mongo ObjectId to strings if present
    for d in docs:
        d.pop("_id", None)
    return docs

@app.post("/products", status_code=201)
def create_product(product: ProductCreate):
    inserted_id = create_document("product", product)
    return {"id": inserted_id}

# Create order endpoint
@app.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    order_id = create_document("order", order)
    return {"id": order_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
