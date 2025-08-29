import os
import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.preprocessing import normalize
import plotly.express as px

# ----------------- Config -----------------
MODEL_NAME = "all-MiniLM-L6-v2"
OUTPUT_DIR = "models"
EMB_FILE = os.path.join(OUTPUT_DIR, "embeddings.npy")
INDEX_FILE = os.path.join(OUTPUT_DIR, "faiss_index.index")  # <-- renamed for FAISS
CLEANED_CSV = os.path.join(OUTPUT_DIR, "cleaned_imdb.csv")

# ----------------- Helpers -----------------
@st.cache_resource(show_spinner=False)
def load_resources():
    if not os.path.exists(EMB_FILE) or not os.path.exists(INDEX_FILE) or not os.path.exists(CLEANED_CSV):
        raise FileNotFoundError("Required files not found. Run build_embeddings.py first.")

    # load embeddings and dataframe
    embeddings = np.load(EMB_FILE).astype("float32")  # FAISS expects float32
    df = pd.read_csv(CLEANED_CSV)

    # normalize embeddings (important for cosine similarity with inner product)
    embeddings = normalize(embeddings, norm="l2").astype("float32")
    dim = embeddings.shape[1]

    # load FAISS index
    index = faiss.read_index(INDEX_FILE)

    # load sentence-transformer model
    model = SentenceTransformer(MODEL_NAME)

    return model, index, embeddings, df

model, index, embeddings, df = load_resources()

# safe encode function with normalization
def encode_text(text):
    vec = model.encode([text], convert_to_numpy=True).astype("float32")
    vec = normalize(vec, norm="l2")  # normalize for cosine similarity
    return vec

def recommend(user_input, top_n=5):
    """
    Returns top_n recommendations as DataFrame with similarity scores.
    Uses FAISS inner product search (with normalized embeddings = cosine).
    """
    if not user_input or not user_input.strip():
        return pd.DataFrame(columns=["Movie Name", "Storyline", "Similarity Score"])

    q_vec = encode_text(user_input)

    # FAISS search (query must be 2D: (1, dim))
    D, I = index.search(q_vec, top_n)

    if len(I[0]) == 0:
        return pd.DataFrame(columns=["Movie Name", "Storyline", "Similarity Score"])

    top_idxs = I[0]
    top_sims = D[0]  # cosine similarity scores

    results = df.iloc[top_idxs].copy().reset_index(drop=True)
    results["Similarity Score"] = top_sims
    return results[["Movie Name", "Storyline", "Similarity Score"]]

# ----------------- Streamlit UI -----------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("<h1 style = 'text-align: center;'>🎬 Movie Recommendation System</h>", unsafe_allow_html=True)
st.markdown("---", unsafe_allow_html=True)

user_input = st.text_area("Enter storyline (or paste a short plot) and get the top 5 semantically similar movies:", height=160)

col1, col2 = st.columns([3,1])
with col2:
    top_n = st.number_input("Top N", min_value=1, max_value=20, value=5, step=1)
    run_button = st.button("🔍 Recommend")

if run_button:
    with st.spinner("Searching..."):
        results = recommend(user_input, top_n=top_n)
    if results.empty:
        st.warning("No recommendations found. Try a different description.")
    else:
        st.success(f"Top {len(results)} Recommendations")
        # display as list + similarity bar chart
        for i, row in results.iterrows():
            st.markdown(f"""
                **🎬 {row['Movie Name']}**
                - 📝 *{row['Storyline']}*
                - 📊 Similarity Score: `{row['Similarity Score'] * 100:.1f}%`
            """)
            st.write("---")

        # Convert to percentage
        results["Similarity (%)"] = (results["Similarity Score"] * 100).round(1)

        #Show Barchart
        fig = px.bar(
            results,
            x="Movie Name",
            y="Similarity (%)",
            text="Similarity (%)",   
            color="Similarity (%)",
            color_continuous_scale="Blues"
        )

        # Improve layout
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            yaxis_title="Similarity (%)",
            xaxis_title="Movie",
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            yaxis=dict(range=[0, 100]),
            title="📊 Similarity Scores"
        )

        st.plotly_chart(fig, use_container_width=True)
