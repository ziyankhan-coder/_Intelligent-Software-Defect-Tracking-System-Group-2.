import re
import nltk

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


# Preserve important negation words
NEGATION_WORDS = {"not", "no", "nor"}

# Load stopwords
stop_words = set(stopwords.words("english"))
stop_words = stop_words - NEGATION_WORDS

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()


def preprocess_text(text):

    if not isinstance(text, str):
        text = str(text)

    # 1. Convert to lowercase
    text = text.lower()

    # 2. Remove special characters and numbers
    text = re.sub(r"[^a-zA-Z\s]", " ", text)

    # 3. Tokenization
    tokens = text.split()

    # 4. Stopword removal and lemmatization
    cleaned_tokens = []

    for word in tokens:

        if word not in stop_words:

            cleaned_word = lemmatizer.lemmatize(word)

            cleaned_tokens.append(cleaned_word)

    # 5. Return cleaned text
    return " ".join(cleaned_tokens)