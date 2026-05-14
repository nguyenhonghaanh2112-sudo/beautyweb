import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_similar_products(target_product, all_products, top_n=4):
    """
    Find similar products using TF-IDF cosine similarity
    on combined brand + name + description + category text.

    Returns list of (Product, similarity_score) tuples.
    """
    if len(all_products) <= 1:
        return []

    # Build text corpus for each product
    def product_text(p):
        parts = [
            str(p.brand or ''),
            str(p.name or ''),
            str(p.description or ''),
            str(p.category or '')
        ]
        return ' '.join(parts).lower()

    corpus = [product_text(p) for p in all_products]

    try:
        vectorizer = TfidfVectorizer(stop_words='english', min_df=1)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Find index of the target product
        target_idx = next(
            (i for i, p in enumerate(all_products) if p.id == target_product.id),
            None
        )

        if target_idx is None:
            return []

        # Compute cosine similarity between target and all products
        scores = cosine_similarity(
            tfidf_matrix[target_idx],
            tfidf_matrix
        ).flatten()

        # Exclude the target product itself
        scores[target_idx] = 0

        # Get top N indices
        top_indices = np.argsort(scores)[::-1][:top_n]

        return [
            (all_products[i], round(float(scores[i]), 3))
            for i in top_indices
            if scores[i] > 0
        ]

    except Exception:
        return []
