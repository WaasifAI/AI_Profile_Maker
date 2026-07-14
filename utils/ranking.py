from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.logger import get_logger

logger = get_logger(__name__)

def rank_results(results: list, query: str, top_k: int = 6):
    if not results:
        return []

    documents = [r.get("content", "") for r in results]
    documents.append(query)  # query goes last, as the reference vector

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)

    query_vector = tfidf_matrix[-1]
    doc_vectors = tfidf_matrix[:-1]

    scores = cosine_similarity(query_vector, doc_vectors).flatten()

    for i, r in enumerate(results):
        r["relevance_score"] = float(scores[i])

    ranked = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    logger.info(f"Ranked {len(ranked)} results, keeping top {top_k}")
    return ranked[:top_k]