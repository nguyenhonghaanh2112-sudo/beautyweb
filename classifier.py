import joblib
import numpy as np
from collections import Counter
import os

# ── Load models once at startup ──────────────────────────────────
BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

try:
    vec_bow        = joblib.load(os.path.join(BASE, "vec_bow.pkl"))
    model_bow      = joblib.load(os.path.join(BASE, "model_logreg_bow.pkl"))
    model_weighted = joblib.load(os.path.join(BASE, "model_logreg_weighted.pkl"))
    idf            = joblib.load(os.path.join(BASE, "idf.pkl"))
    wv_dict        = joblib.load(os.path.join(BASE, "wv_dict.pkl"))
    EMB_DIM        = len(next(iter(wv_dict.values())))
    MODELS_LOADED  = True
    print("✅ All ML models loaded successfully")
except Exception as e:
    print(f"⚠️  Could not load ML models: {e}")
    MODELS_LOADED = False


# ── Text preprocessing (mirrors Task 1 pipeline) ─────────────────
def preprocess_text(text):
    """Simple tokenization matching Task 1 pipeline."""
    import re
    text = text.lower()
    tokens = re.findall(r"[a-z]+(?:[-'][a-z]+)?", text)
    tokens = [t for t in tokens if len(t) >= 2]
    return tokens


# ── FastText weighted document vector ────────────────────────────
def doc_vector_weighted(tokens):
    tf = Counter(tokens)
    weighted_sum = np.zeros(EMB_DIM, dtype=float)
    total_weight = 0.0
    for w, tf_w in tf.items():
        if w in wv_dict:
            weight = tf_w * idf.get(w, 1.0)
            weighted_sum += weight * wv_dict[w]
            total_weight += weight
    if total_weight == 0:
        return np.zeros(EMB_DIM)
    return weighted_sum / total_weight


# ── Main prediction function ──────────────────────────────────────
def predict_label(review_title, review_text, rating):
    """
    Fuse 3 models to predict recommendation label (0 or 1).
    Returns (label, confidence_score).
    """
    if not MODELS_LOADED:
        # Fallback: simple heuristic if models not available
        label = 1 if rating >= 4 else 0
        return label, float(rating / 5)

    try:
        combined = f"{review_title} {review_text}"

        # ── Model 1: BoW (CountVectorizer + LogReg) ──────────────
        X1 = vec_bow.transform([combined])
        prob1 = model_bow.predict_proba(X1)[0][1]

        # ── Model 2: TF-IDF weighted FastText + LogReg ───────────
        tokens = preprocess_text(review_text)
        if tokens:
            X2 = doc_vector_weighted(tokens).reshape(1, -1)
            prob2 = model_weighted.predict_proba(X2)[0][1]
        else:
            prob2 = prob1   # fallback if tokenization produces nothing

        # ── Model 3: Rating heuristic ────────────────────────────
        prob3 = min(1.0, max(0.0, (rating - 1) / 4))

        # ── Weighted fusion ──────────────────────────────────────
        fused = 0.45 * prob1 + 0.45 * prob2 + 0.10 * prob3

        label = int(fused >= 0.5)
        return label, round(float(fused), 3)

    except Exception as e:
        print(f"Prediction error: {e}")
        label = 1 if rating >= 4 else 0
        return label, float(rating / 5)
