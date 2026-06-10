import numpy as np
import os
import pickle

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Bidirectional, Dense, TimeDistributed
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.utils import to_categorical

# ------------------ PATHS ------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "disease_ner", "train.bio")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)

# ------------------ LOAD BIO DATA ------------------

def load_bio_data(filepath):
    sentences, labels = [], []
    words, tags = [], []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if words:
                    sentences.append(words)
                    labels.append(tags)
                    words, tags = [], []
            else:
                w, t = line.split()
                words.append(w)
                tags.append(t)

    return sentences, labels


sentences, labels = load_bio_data(DATA_PATH)

# ------------------ TOKENIZER ------------------

tokenizer = Tokenizer(lower=True, oov_token="<OOV>")
tokenizer.fit_on_texts(sentences)

X = tokenizer.texts_to_sequences(sentences)

# ------------------ TAG MAPPING ------------------

tag_set = sorted({tag for seq in labels for tag in seq})
tag2idx = {tag: i for i, tag in enumerate(tag_set)}
idx2tag = {i: tag for tag, i in tag2idx.items()}

y = [[tag2idx[tag] for tag in seq] for seq in labels]

# ------------------ PADDING ------------------

MAX_LEN = max(len(seq) for seq in X)

X = pad_sequences(X, maxlen=MAX_LEN, padding="post")
y = pad_sequences(y, maxlen=MAX_LEN, padding="post")
y = np.array([to_categorical(seq, num_classes=len(tag2idx)) for seq in y])

# ------------------ MODEL ------------------

model = Sequential([
    Embedding(input_dim=len(tokenizer.word_index) + 1, output_dim=64, input_length=MAX_LEN),
    Bidirectional(LSTM(64, return_sequences=True)),
    TimeDistributed(Dense(len(tag2idx), activation="softmax"))
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# ------------------ TRAIN ------------------

model.fit(X, y, batch_size=16, epochs=15, validation_split=0.1)

# ------------------ SAVE EVERYTHING ------------------

model.save(os.path.join(MODEL_DIR, "disease_ner_model.keras"))

with open(os.path.join(MODEL_DIR, "tokenizer.pkl"), "wb") as f:
    pickle.dump(tokenizer, f)

np.save(os.path.join(MODEL_DIR, "tag2idx.npy"), tag2idx)
np.save(os.path.join(MODEL_DIR, "idx2tag.npy"), idx2tag)

print("✅ Disease NER model + tokenizer saved successfully")
