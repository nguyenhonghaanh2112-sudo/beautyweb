from flask import render_template, request, redirect, url_for
from app import app, db
from models_db import Product, Review
from utils.search import search_products
from utils.classifier import predict_label
from utils.recommender import get_similar_products


# ── Home Page ────────────────────────────────────────────────────
@app.route("/")
def index():
    # Get unique brands for filter pills (not product names!)
    brands = db.session.query(Product.brand).distinct().order_by(Product.brand).all()
    brands = [b[0] for b in brands if b[0] and b[0].strip()]

    selected_brand = request.args.get("brand", "")

    if selected_brand:
        products = Product.query.filter_by(brand=selected_brand).all()
    else:
        products = Product.query.all()

    return render_template("index.html",
                           products=products,
                           brands=brands,
                           selected_brand=selected_brand)


# ── Search ───────────────────────────────────────────────────────
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect(url_for("index"))
    results = search_products(query)
    return render_template("search.html",
                           results=results,
                           query=query,
                           count=len(results))


# ── Product Detail ───────────────────────────────────────────────
@app.route("/product/<int:pid>")
def product_detail(pid):
    product = Product.query.get_or_404(pid)
    reviews = Review.query.filter_by(product_id=pid).order_by(Review.id.desc()).all()

    all_products = Product.query.all()
    similar = get_similar_products(product, all_products, top_n=4)

    avg_rating = 0
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)

    return render_template("product.html",
                           product=product,
                           reviews=reviews,
                           similar=similar,
                           avg_rating=avg_rating)


# ── Add Review (Form) ────────────────────────────────────────────
@app.route("/product/<int:pid>/review", methods=["GET", "POST"])
def add_review(pid):
    product = Product.query.get_or_404(pid)

    if request.method == "POST":
        title  = request.form.get("title", "")
        text   = request.form.get("text", "")
        rating = int(request.form.get("rating", 3))

        label, confidence = predict_label(title, text, rating)

        return render_template("review_confirm.html",
                               product=product,
                               title=title,
                               text=text,
                               rating=rating,
                               label=label,
                               confidence=confidence)

    return render_template("review_form.html", product=product)


# ── Confirm Review (Save to DB) ──────────────────────────────────
@app.route("/product/<int:pid>/review/confirm", methods=["POST"])
def confirm_review(pid):
    product = Product.query.get_or_404(pid)

    original_label = int(request.form.get("original_label", 0))
    final_label    = int(request.form.get("final_label", original_label))

    review = Review(
        product_id      = pid,
        title           = request.form.get("title", ""),
        text            = request.form.get("text", ""),
        rating          = int(request.form.get("rating", 3)),
        recommend_label = final_label,
        user_overridden = (final_label != original_label)
    )
    db.session.add(review)
    db.session.commit()

    return redirect(url_for("product_detail", pid=pid))


# ── Admin Dashboard (Task 4) ─────────────────────────────────────
@app.route("/admin")
def admin_dashboard():
    total_products = Product.query.count()
    total_reviews  = Review.query.count()
    positive       = Review.query.filter_by(recommend_label=1).count()
    negative       = Review.query.filter_by(recommend_label=0).count()
    overridden     = Review.query.filter_by(user_overridden=True).count()

    brands = db.session.query(Product.brand).distinct().all()
    cat_stats = []
    for (brand,) in brands:
        if not brand:
            continue
        prods    = Product.query.filter_by(brand=brand).all()
        prod_ids = [p.id for p in prods]
        rev_count = Review.query.filter(Review.product_id.in_(prod_ids)).count()
        pos_count = Review.query.filter(
            Review.product_id.in_(prod_ids),
            Review.recommend_label == 1
        ).count()
        cat_stats.append({
            "category": brand,
            "products": len(prods),
            "reviews":  rev_count,
            "positive": pos_count,
            "pct": round(pos_count / rev_count * 100, 1) if rev_count > 0 else 0
        })

    return render_template("admin.html",
                           total_products=total_products,
                           total_reviews=total_reviews,
                           positive=positive,
                           negative=negative,
                           overridden=overridden,
                           cat_stats=cat_stats)
