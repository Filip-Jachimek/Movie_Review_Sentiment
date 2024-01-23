# 🔴 Projekt update programu:

# python project.py train
# python project.py report "This is awful movie!"


import csv
import glob
import pickle
import os

import re

import pymongo
import click

TRAIN_FILES_FOLDER = "data/aclimdb/train"
CSV_ALL_REVIEWS_COMBINED = 'all_reviews_combined.csv'
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
    
def extract_info_from_filename(filename):
    print("Hey, I was executed!")
    match = re.match(r'(\d+)_(\d+)(?:_\d+)?\.txt', filename)
    if match:
        index_part, rate_part = match.groups()
        print(f"Matched: Filename: {filename}, Index Part: {index_part}, Rate Part: {rate_part}")
        try:
            index = int(index_part)
            rate = int(rate_part)
            return index, rate
        except ValueError as ve:
            print(f"Error converting parts to integers: {ve}")
            return None, None
    else:
        print(f"No Match: Filename: {filename}")
        return None, None

def merge_to_csv():
    with open(CSV_ALL_REVIEWS_COMBINED, 'w', encoding='utf-8', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['index', 'rate', 'description', 'label'])
        
        for folder in os.listdir(TRAIN_FILES_FOLDER):
            folder_path = os.path.join(TRAIN_FILES_FOLDER, folder)
            label = 'positive' if 'pos' in folder else 'negative'
            for file in glob.glob(os.path.join(folder_path, '*.txt')):
                try:
                    print(f"Processing file: {file}")
                    with open(file, encoding='utf-8') as stream:
                        content = stream.read()
                        filename = os.path.basename(file)
                        index, rate = extract_info_from_filename(filename)
                        
                        if index is not None and rate is not None:
                            # Write each piece of information as a separate column
                            csv_writer.writerow([index, rate, content, label])
                            print(f"Processed: {filename}")
                        else:
                            print(f"Skipping {filename} due to invalid index or rate.")
                except Exception as e:
                    print(f"Error processing file {file}: {e}")

    print("Merging completed.")

@click.group()
def cli():
    pass

@cli.command()
def train() -> dict:
    
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


@cli.command()
def merge_command():
    merge_to_csv()
    




@cli.command()
@click.option('--connection_string', prompt=True, help='MongoDB connection string')
@click.option('--database_name', prompt=True, help='Name of the MongoDB database')
@click.option('--collection_name', prompt=True, help='Name of the MongoDB collection')
@click.argument('csv_file', type=click.Path(exists=True))
def upload_to_mongodb(connection_string, database_name, collection_name, csv_file):
    """Upload CSV file to MongoDB."""
    client = pymongo.MongoClient(connection_string)
    db = client[database_name]
    collection = db[collection_name]

    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        documents = list(csv_reader)

    collection.insert_many(documents)
    click.echo(f'{len(documents)} files uploaded to MongoDB.')

# ... Other Click commands and functions ...

if __name__ == "__main__":
    cli()
