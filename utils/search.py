import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models_db import Product


def normalize(text):
    """Lowercase, strip extra spaces."""
    return re.sub(r'\s+', ' ', str(text).lower().strip())


def search_products(query):
    """
    TF-IDF cosine similarity search across brand + name + description.
    Falls back to token matching for very short queries.
    Returns list of Product objects ranked by relevance.
    """
    if not query:
        return []

    products = Product.query.all()
    if not products:
        return []

    q = normalize(query)

    # Build corpus: one string per product
    corpus = [
        normalize(f"{p.brand or ''} {p.name or ''} {p.description or ''}")
        for p in products
    ]

    # Append query as the last document
    corpus.append(q)

    try:
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',   # character n-grams handle typos
            ngram_range=(2, 4),
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

        # Return products with score > 0, ranked best first
        ranked = sorted(
            [(products[i], scores[i]) for i in range(len(products)) if scores[i] > 0],
            key=lambda x: -x[1]
        )
        return [p for p, s in ranked]

    except Exception:
        # Fallback: simple token matching
        tokens = q.split()
        results = []
        for p in products:
            haystack = normalize(f"{p.brand} {p.name} {p.description}")
            if any(tok in haystack for tok in tokens):
                results.append(p)
        return results
