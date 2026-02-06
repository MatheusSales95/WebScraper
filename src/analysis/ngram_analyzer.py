from nltk import ngrams
from nltk.corpus import stopwords
from collections import Counter


class NGramAnalyzer:
    def __init__(self, language='portuguese'):
        self.stop_words = set(stopwords.words(language))

    def is_valid_ngram(self, ngram_tuple):
        """
        Um N-Gram é útil se NÃO começa nem termina com stopword.
        Ex: 'banco de dados' (Válido: começa/termina com substantivo)
        Ex: 'de dados' (Inválido: começa com stopword)
        Ex: 'banco de' (Inválido: termina com stopword)
        """
        # Se todos os termos forem stopwords, descarta (ex: "de para")
        if all(w in self.stop_words for w in ngram_tuple):
            return False

        # Filtro de borda: O primeiro e o último termo devem ser palavras de conteúdo
        if ngram_tuple[0] in self.stop_words or ngram_tuple[-1] in self.stop_words:
            return False

        return True

    def generate_ngrams(self, tokens_raw, n=2, top_k=10):
        """
        Gera N-Grams a partir dos tokens brutos (com ordem correta)
        e aplica filtro de qualidade.
        """
        if not tokens_raw or len(tokens_raw) < n:
            return []

        # 1. Gera todos os n-grams possíveis (incluindo "de", "da")
        # tokens_raw deve vir em minúsculo do tokenizer
        raw_ngrams = ngrams(tokens_raw, n)

        # 2. Filtra apenas os gramaticalmente ricos
        valid_ngrams = [
            gram for gram in raw_ngrams
            if self.is_valid_ngram(gram)
        ]

        # 3. Contagem
        count = Counter(valid_ngrams)

        return [
            {"term": " ".join(gram), "count": freq}
            for gram, freq in count.most_common(top_k)
        ]
