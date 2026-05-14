"""
seed.py — Run once to populate the database from your CSV.
Usage: python seed.py
"""

import pandas as pd
from app import app
from models_db import db, Product, Review

# ── Column name mapping ───────────────────────────────────────────
# Adjust these to match your actual CSV column names
CSV_PATH = "data/cosmetics_beauty_products_reviews.csv"

with app.app_context():
    db.create_all()

    # Skip if already seeded
    if Product.query.count() > 0:
        print("Database already seeded. Skipping.")
        exit()

    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows from CSV")
    print("Columns:", df.columns.tolist())

    # ── Deduplicate by product ────────────────────────────────────
    # Adjust column names to match your CSV
    product_col   = "product_title"     # product name column
    brand_col     = "brand_name"        # brand column
    desc_col      = "review_text"       # use review as description fallback
    category_col  = "product_title"     # or a real category column if exists

    # Build unique products
    product_map = {}   # product_name -> Product id

    for _, row in df.iterrows():
        name = str(row.get(product_col, "Unknown Product"))[:200]

        if name not in product_map:
            product = Product(
                name        = name,
                brand       = str(row.get(brand_col, ""))[:100],
                description = str(row.get(desc_col, ""))[:500],
                category    = str(row.get(category_col, "Beauty"))[:100],
                image_url   = ""   # no real images in CSV — placeholder used
            )
            db.session.add(product)
            db.session.flush()   # get product.id before commit
            product_map[name] = product.id

    db.session.commit()
    print(f"✅ Inserted {len(product_map)} products")

    # ── Seed reviews ─────────────────────────────────────────────
    review_count = 0
    for _, row in df.iterrows():
        name = str(row.get(product_col, "Unknown Product"))[:200]
        pid  = product_map.get(name)
        if not pid:
            continue

        # Parse is_a_buyer label
        raw_label = str(row.get("is_a_buyer", "false")).lower().strip()
        label = 1 if raw_label in ("true", "1", "yes") else 0

        # Parse rating (1-5)
        try:
            rating = int(float(row.get("product_rating", 3)))
            rating = max(1, min(5, rating))
        except (ValueError, TypeError):
            rating = 3

        review = Review(
            product_id      = pid,
            title           = str(row.get("review_title", "Review"))[:200],
            text            = str(row.get("review_text", ""))[:2000],
            rating          = rating,
            recommend_label = label,
            user_overridden = False
        )
        db.session.add(review)
        review_count += 1

        # Commit in batches to avoid memory issues
        if review_count % 500 == 0:
            db.session.commit()
            print(f"  {review_count} reviews inserted...")

    db.session.commit()
    print(f"✅ Inserted {review_count} reviews")
    print("🎉 Database seeding complete!")
