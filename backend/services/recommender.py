# ==============================================================================
# SERVICES — Anime Recommendation Engine (TF-IDF Cosine Similarity)
# ==============================================================================
# Purpose:
#     Provides content-based anime recommendations using a lightweight
#     TF-IDF vectorizer and cosine similarity scorer. No external ML
#     dependencies required — implements the algorithm from scratch.
#
# Need:
#     Powers the "AI Recommender" feature that matches natural language
#     plot descriptions against a corpus of anime metadata to suggest
#     relevant shows. Also provides index-based "similar anime"
#     recommendations on detail pages.
#
# Architecture Note:
#     Moved from backend/recommender.py into the services package to
#     follow the single-responsibility layered architecture.
# ==============================================================================

import re
import math


def is_hentai(item):
    """
    Determine if an anime item is classified as hentai/adult content.

    Detailed Use:
        Checks multiple signals: slug prefix ('hanime:'), id prefix,
        genre lists, tag lists, and title/description text for the
        keyword 'hentai'.

    Need:
        Required by the content filtering pipeline to identify adult
        content for probabilistic filtering and demotion in homepage
        feeds and search results.

    Args:
        item (dict or any): The anime metadata dictionary to check.

    Returns:
        bool: True if the item is classified as hentai.
    """
    if not isinstance(item, dict):
        return False
    slug = str(item.get("slug", ""))
    item_id = str(item.get("id", ""))
    if slug.startswith("hanime:") or item_id.startswith("hanime:"):
        return True
    genres = [str(g).lower() for g in (item.get("genres") or [])]
    if "hentai" in genres:
        return True
    tags = [str(t).lower() for t in (item.get("tags") or [])]
    if "hentai" in tags:
        return True
    title = str(item.get("title", "")).lower()
    desc = str(item.get("description", "") or item.get("synopsis", "")).lower()
    if "hentai" in title or "hentai" in desc:
        return True
    return False


class AnimeRecommender:
    """
    Content-based recommendation engine using TF-IDF and cosine similarity.

    Detailed Use:
        Builds TF-IDF vectors from anime title + genre + description text,
        then computes pairwise cosine similarity to rank recommendations.
        Hentai items receive a 0.15x score penalty to demote them in
        non-explicit contexts.

    Need:
        Enables the "Describe what you want to watch" and "Similar anime"
        features without requiring heavy ML dependencies like scikit-learn.
        The entire algorithm runs in-process with O(n*m) complexity where
        n = corpus size and m = vocabulary size.
    """

    def __init__(self):
        """Initialize the recommender (stateless — no precomputation needed)."""
        pass

    def _tokenize(self, text):
        """
        Tokenize text into lowercase alphanumeric words.

        Detailed Use:
            Converts text to lowercase, strips non-alphanumeric characters,
            and splits on whitespace.

        Need:
            Standard text preprocessing step for TF-IDF vectorization.

        Args:
            text (str): Raw text to tokenize.

        Returns:
            list[str]: List of lowercase word tokens.
        """
        if not text:
            return []
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return [w for w in text.split() if w]

    def _get_tf_idf_vectors(self, corpus):
        """
        Compute TF-IDF vectors for a list of text documents.

        Detailed Use:
            Calculates term frequency (TF) normalized by document length,
            inverse document frequency (IDF) using the standard log formula,
            and multiplies them to produce sparse TF-IDF vectors (dicts).

        Need:
            TF-IDF weighting ensures that common words (e.g., 'anime',
            'the') are down-weighted while distinctive terms (e.g.,
            'mecha', 'isekai') carry more matching power.

        Args:
            corpus (list[str]): List of document strings.

        Returns:
            list[dict]: List of sparse TF-IDF vectors (word -> weight).
        """
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]

        # Calculate document frequency for each word
        df = {}
        for doc in tokenized_corpus:
            unique_words = set(doc)
            for word in unique_words:
                df[word] = df.get(word, 0) + 1

        # Calculate inverse document frequency
        num_docs = len(corpus)
        idf = {}
        for word, count in df.items():
            idf[word] = math.log(1.0 + num_docs / (1.0 + count)) + 1.0

        # Calculate TF-IDF vectors
        vectors = []
        for doc in tokenized_corpus:
            tf = {}
            for word in doc:
                tf[word] = tf.get(word, 0) + 1
            doc_len = len(doc)
            vector = {}
            if doc_len > 0:
                for word, count in tf.items():
                    vector[word] = (count / doc_len) * idf.get(word, 0.0)
            vectors.append(vector)

        return vectors

    def _cosine_similarity(self, vec1, vec2):
        """
        Compute cosine similarity between two sparse vectors.

        Detailed Use:
            Calculates the dot product divided by the product of L2 norms.
            Returns 0.0 if either vector has zero magnitude.

        Need:
            The core similarity metric for ranking how closely a query
            document matches each candidate in the corpus.

        Args:
            vec1 (dict): First sparse vector (word -> weight).
            vec2 (dict): Second sparse vector (word -> weight).

        Returns:
            float: Cosine similarity in range [0.0, 1.0].
        """
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
        """
        Find anime matching a natural language description.

        Detailed Use:
            Appends the user's description to the anime corpus, computes
            TF-IDF vectors for all documents, then ranks anime by cosine
            similarity to the description vector. Hentai items receive
            a 0.15x score penalty.

        Need:
            Powers the "Describe what you want to watch" feature — lets
            users discover anime by mood, setting, or narrative tropes
            rather than exact title search.

        Args:
            description (str): The user's natural language query.
            anime_data (list[dict]): List of anime metadata dictionaries.
            top_n (int): Maximum number of recommendations to return.

        Returns:
            list[dict]: Top-N recommended anime, sorted by relevance.
        """
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
                if is_hentai(anime_data[idx]):
                    sim *= 0.15
                scores.append((sim, idx))

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
        """
        Find anime similar to a specific item in the dataset.

        Detailed Use:
            Uses the anime at anime_index as the query vector and ranks
            all other anime by cosine similarity. Hentai items receive
            a 0.15x score penalty.

        Need:
            Powers the "Similar Anime" recommendations on detail pages,
            helping users discover related shows.

        Args:
            anime_index (int): Index of the target anime in anime_data.
            anime_data (list[dict]): List of anime metadata dictionaries.
            top_n (int): Maximum number of recommendations to return.

        Returns:
            list[dict]: Top-N similar anime, sorted by relevance.
        """
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
                if is_hentai(anime_data[idx]):
                    sim *= 0.15
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
    """
    Attempt to find a local scraper slug for a given anime title.

    Detailed Use:
        Placeholder for future cross-referencing logic that would map
        Jikan/MAL titles to locally scraped slugs for direct playback.

    Need:
        Currently returns None. When implemented, it would allow
        recommendations from Jikan to link directly to playable
        scraper pages instead of search fallbacks.

    Args:
        title (str): The anime title to look up.

    Returns:
        str or None: The local slug, or None if not found.
    """
    return None
