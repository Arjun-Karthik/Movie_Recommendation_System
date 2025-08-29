import os
import numpy as np
import pandas as pd
import re
import string
import nltk
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import faiss
from nltk.corpus import stopwords

# ----------------- Config -----------------
DATA_CSV = "IMDB_Movies_Data.csv"   # <- replace with your CSV (must contain "Movie Name" and "Storyline")
OUTPUT_DIR = "models"
EMB_FILE = os.path.join(OUTPUT_DIR, "embeddings.npy")
INDEX_FILE = os.path.join(OUTPUT_DIR, "faiss_index.index")
CLEANED_CSV = os.path.join(OUTPUT_DIR, "cleaned_imdb.csv")

MODEL_NAME = "all-MiniLM-L6-v2"  # small & fast; swap for larger model if desired
BATCH_SIZE = 64
N_TREES = 50                      # increase for better accuracy (slower build)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------- Download NLTK stopwords -----------------
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

# ----------------- Text cleaning (same pipeline you used before) -----------------
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"\d+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = " ".join([w for w in text.split() if w not in stop_words])
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ----------------- Load & clean dataset -----------------
print("Loading dataset:", DATA_CSV)
df = pd.read_csv(DATA_CSV)
if "Storyline" not in df.columns:
    raise ValueError("CSV must contain a 'Storyline' column")

print("Cleaning storylines...")
df["Storyline"] = df["Storyline"].fillna("").astype(str).apply(clean_text)

# Save cleaned dataframe
df.to_csv(CLEANED_CSV, index=False)
print("Saved cleaned dataframe to", CLEANED_CSV)

# ----------------- Build sentence embeddings -----------------
print("Loading SentenceTransformer model:", MODEL_NAME)
model = SentenceTransformer(MODEL_NAME)

texts = df["Storyline"].tolist()
n = len(texts)
print(f"Encoding {n} storylines with batch_size={BATCH_SIZE} ...")

# encode in batches (SentenceTransformer does batching internally, but this shows progress)
embeddings = model.encode(texts,
                          batch_size=BATCH_SIZE,
                          show_progress_bar=True,
                          convert_to_numpy=True)

# Normalize embeddings (L2) so cosine similarity = dot product
embeddings = normalize(embeddings, norm="l2")

# Save embeddings to disk
print("Saving embeddings to", EMB_FILE)
np.save(EMB_FILE, embeddings.astype(np.float32))  # save as float32 to reduce size

# ----------------- Build FAISS index -----------------
dim = embeddings.shape[1]
print(f"Building FAISS index (dim={dim}) ...")

# IndexFlatIP = Inner Product (cosine similarity since vectors are normalized)
faiss_index = faiss.IndexFlatIP(dim)
faiss_index.add(embeddings)   # add all vectors

# Save FAISS index
faiss.write_index(faiss_index, INDEX_FILE)
print("FAISS index saved to", INDEX_FILE)

print("✅ Done. Artifacts saved in folder:", OUTPUT_DIR)
