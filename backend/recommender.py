import re
import time
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class AnimeRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")

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
            vectors = self.vectorizer.fit_transform(corpus)
            scores = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
            ranked = scores.argsort()[::-1]
            
            results = []
            for idx in ranked:
                if scores[idx] <= 0:
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
                
            vectors = self.vectorizer.fit_transform(corpus)
            scores = cosine_similarity(vectors[anime_index], vectors).flatten()
            ranked = scores.argsort()[::-1]
            results = []
            for idx in ranked:
                if idx == anime_index:
                    continue
                results.append(anime_data[idx])
                if len(results) >= top_n:
                    break
            return results
        except Exception as e:
            print("Error in recommend:", e)
            return anime_data[:top_n]


def find_local_slug_by_title(title):
    return None
