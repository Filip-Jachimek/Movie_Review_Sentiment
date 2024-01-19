# 🔴 Projekt update programu:

# python project.py train
# python project.py report "This is awful movie!"


import glob
import pickle

import click

POS_FILES_FOLDER = "data/aclimdb/train/pos/*.txt"
NEG_FILES_FOLDER = "data/aclimdb/train/neg/*.txt"
POS_DB_FILENAME = "trained_pos_reviews.csv"
NEG_DB_FILENAME = "trained_neg_reviews.csv"

def preprocess_review(review):
    """Return a list or words"""
    return review.lower().replace('<br />', ' ').split()


def count_words(path_pattern):
    words_count = {}
    files = glob.glob(path_pattern)
    for file in files:
        with open(file, encoding='utf-8') as stream:
            content = stream.read()
            words = preprocess_review(content)
            for word in set(words):
                words_count[word] = words_count.get(word, 0) + 1
    return words_count


def compute_sentiment(words, words_count_pos, words_count_neg, debug=False):
    sentence_sentiment = 0
    for word in words:
        positive = words_count_pos.get(word, 0)
        negative = words_count_neg.get(word, 0)

        all_ = positive + negative
        if all_ == 0:
            word_sentiment = 0.0
        else:
            word_sentiment = (positive - negative) / all_
        if debug:
            print(word, word_sentiment)
        sentence_sentiment += word_sentiment
    sentence_sentiment /= len(words)
    return sentence_sentiment


def print_sentient(sentiment):
    if sentiment > 0:
        label = 'positive'
    else:
        label = 'negative'
        print('------------')
    print("This sentence is", label, ', sentiment =', sentiment)

def save_train_result(trained_files: dict, DB_FILENAME) -> None:
    with open(DB_FILENAME, 'wb') as stream:
        trained_files = pickle.dump(trained_files, stream)

def load_train_result(db_path) -> dict:
    try:
        with open(db_path, 'rb') as stream:
            train_result = pickle.load(stream)
    except FileNotFoundError:
        print ('Train program first!')
    
    return train_result
    
@click.group()
def cli():
    pass

@cli.command()
def train() -> dict(str, float):
    
    print("I started training myself in positive comments")
    words_count_pos = count_words(POS_FILES_FOLDER)
    save_train_result(words_count_pos, POS_DB_FILENAME)
    print("I finished training in positive, now in negativity")
    words_count_neg = count_words(NEG_FILES_FOLDER)
    save_train_result(words_count_neg, NEG_DB_FILENAME)
    print("I finished all training, now enter comments")

@cli.command()
@click.argument('new_review', type=str)
def report(new_review) -> str:
    words_count_pos = load_train_result(POS_DB_FILENAME)
    words_count_neg = load_train_result(NEG_DB_FILENAME)
    words = preprocess_review(new_review)
    sentiment = compute_sentiment(
        words, words_count_pos, words_count_neg, debug=True)
    print('==')
    print_sentient(sentiment)

if __name__ == "__main__":
    cli()
