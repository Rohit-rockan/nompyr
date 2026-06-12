import re
import math

class AnimeRecommender:
    def __init__(self):
        pass

    def _tokenize(self, text):
        if not text:
            return []
        text = text.lower()
        # Keep alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return [w for w in text.split() if w]

    def _get_tf_idf_vectors(self, corpus):
        # corpus is a list of strings
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        
        # Calculate DF (document frequency) for each word
        df = {}
        for doc in tokenized_corpus:
            unique_words = set(doc)
            for word in unique_words:
                df[word] = df.get(word, 0) + 1
                
        # Calculate IDF (inverse document frequency)
        num_docs = len(corpus)
        idf = {}
        for word, count in df.items():
            # Standard IDF formula: ln(1 + num_docs / (1 + count))
            idf[word] = math.log(1.0 + num_docs / (1.0 + count)) + 1.0
            
        # Calculate TF-IDF vectors
        vectors = []
        for doc in tokenized_corpus:
            tf = {}
            for word in doc:
                tf[word] = tf.get(word, 0) + 1
            # Normalize term frequency or just use raw count
            doc_len = len(doc)
            vector = {}
            if doc_len > 0:
                for word, count in tf.items():
                    vector[word] = (count / doc_len) * idf.get(word, 0.0)
            vectors.append(vector)
            
        return vectors

    def _cosine_similarity(self, vec1, vec2):
        # Compute dot product and norms
        dot_product = 0.0
        for word, val in vec1.items():
            if word in vec2:
                dot_product += val * vec2[word]
                
        norm1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

    def recommend_by_description(self, description, anime_data, top_n=12):
        if not anime_data or not description:
            return []
            
        corpus = []
        for anime in anime_data:
            title = anime.get("title", "")
            genres = " ".join(anime.get("genres", []))
            desc = anime.get("description", "") or anime.get("synopsis", "") or ""
            corpus.append(f"{title} {genres} {desc}")
            
        corpus.append(description)
        
        try:
            vectors = self._get_tf_idf_vectors(corpus)
            query_vector = vectors[-1]
            doc_vectors = vectors[:-1]
            
            scores = []
            for idx, vec in enumerate(doc_vectors):
                sim = self._cosine_similarity(query_vector, vec)
                scores.append((sim, idx))
                
            # Sort by similarity descending
            scores.sort(key=lambda x: x[0], reverse=True)
            
            results = []
            for sim, idx in scores:
                if sim <= 0:
                    continue
                results.append(anime_data[idx])
                if len(results) >= top_n:
                    break
            return results
        except Exception as e:
            print("Error in recommend_by_description:", e)
            return anime_data[:top_n]

    def recommend(self, anime_index, anime_data, top_n=12):
        try:
            corpus = []
            for anime in anime_data:
                title = anime.get("title", "")
                genres = " ".join(anime.get("genres", []))
                desc = anime.get("description", "") or anime.get("synopsis", "") or ""
                corpus.append(f"{title} {genres} {desc}")
                
            vectors = self._get_tf_idf_vectors(corpus)
            target_vector = vectors[anime_index]
            
            scores = []
            for idx, vec in enumerate(vectors):
                if idx == anime_index:
                    continue
                sim = self._cosine_similarity(target_vector, vec)
                scores.append((sim, idx))
                
            scores.sort(key=lambda x: x[0], reverse=True)
            results = []
            for sim, idx in scores:
                results.append(anime_data[idx])
                if len(results) >= top_n:
                    break
            return results
        except Exception as e:
            print("Error in recommend:", e)
            return anime_data[:top_n]


def find_local_slug_by_title(title):
    return None
