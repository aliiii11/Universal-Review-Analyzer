# src/analyze_reviews.py
import os, json, ast
import pandas as pd
from textblob import TextBlob

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

INPUT_PATH  = os.path.join(DATA_DIR, "collected_reviews.csv")
OUTPUT_PATH = os.path.join(DATA_DIR, "analyzed_reviews.csv")

def _ensure_analyzed_file():
    if not os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
            pd.DataFrame(columns=[
                "product","review","sentiment","pros","cons","improvements","verdict"
            ]).to_csv(f, index=False)

def _sentiment(text: str):
    blob = TextBlob(str(text))
    p = blob.sentiment.polarity
    if p > 0.1:  return "Positive"
    if p < -0.1: return "Negative"
    return "Neutral"

_PROS = ["good","great","excellent","easy","useful","fast","quality","comfortable","battery","camera","display","value"]
_CONS = ["bad","slow","poor","difficult","hard","expensive","problem","issue","worst","lag","heating","overpriced","bug"]

def _pros(text): return [w for w in _PROS if w in str(text).lower()]
def _cons(text): return [w for w in _CONS if w in str(text).lower()]

def _improvements(cons_list):
    cons_set = set(cons_list or [])
    sugg = []
    if {"slow","lag"} & cons_set:        sugg.append("Improve performance/speed.")
    if {"expensive","overpriced"} & cons_set: sugg.append("Reduce price / add offers.")
    if {"heating"} & cons_set:          sugg.append("Thermal optimization.")
    if {"bug","issue","problem"} & cons_set:  sugg.append("Stability fixes.")
    if {"poor","bad","worst"} & cons_set:     sugg.append("Quality/reliability improvements.")
    return list(dict.fromkeys(sugg))

def _build_verdict(sent_counts: pd.Series):
    total = int(sent_counts.sum() or 1)
    pos = int(sent_counts.get("Positive", 0))
    neg = int(sent_counts.get("Negative", 0))
    neu = int(sent_counts.get("Neutral",  0))
    pos_pct = round(100*pos/total, 1)
    neg_pct = round(100*neg/total, 1)
    mood = "Mostly Positive" if pos_pct >= 55 else ("Mostly Negative" if neg_pct >= 55 else "Mixed")
    return f"{mood} — {pos_pct}% Positive, {neg_pct}% Negative, {round(100-pos_pct-neg_pct,1)}% Neutral"

def analyze_reviews(product_filter: str | None = None):
    """
    Reads collected_reviews.csv, optionally filters by product,
    computes per-review fields + a unified verdict, returns analyzed df,
    and appends new rows to analyzed_reviews.csv (dedup on product+review).
    """
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"{INPUT_PATH} not found! Run Day 1 first to collect reviews.")

    df = pd.read_csv(INPUT_PATH)
    if df.empty:
        return pd.DataFrame()

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()   # product, site, url, review

    if "review" not in df.columns or "product" not in df.columns:
        raise ValueError("Input CSV must have 'Product' and 'Review' columns.")

    if product_filter:
        df = df[df["product"].str.lower() == product_filter.lower()]

    if df.empty:
        return pd.DataFrame()

    # Per-review fields
    analyzed = pd.DataFrame({
        "product": df["product"],
        "review": df["review"]
    })
    analyzed["sentiment"]    = analyzed["review"].apply(_sentiment)
    analyzed["pros"]         = analyzed["review"].apply(_pros)
    analyzed["cons"]         = analyzed["review"].apply(_cons)
    analyzed["improvements"] = analyzed["cons"].apply(_improvements)

    # Single verdict for the analyzed set
    verdict = _build_verdict(analyzed["sentiment"].value_counts())
    analyzed["verdict"] = verdict

    # Persist with dedupe on (product, review)
    _ensure_analyzed_file()
    try:
        existing = pd.read_csv(OUTPUT_PATH)
        if not existing.empty:
            key = existing[["product","review"]].astype(str).agg("||".join, axis=1)
            existing_keys = set(key.tolist())
        else:
            existing_keys = set()
    except Exception:
        existing_keys = set()

    mask_new = ~analyzed.astype(str)[["product","review"]].agg("||".join, axis=1).isin(existing_keys)
    to_append = analyzed[mask_new]

    if not to_append.empty:
        to_append.to_csv(OUTPUT_PATH, mode="a", header=not os.path.getsize(OUTPUT_PATH), index=False)

    return analyzed