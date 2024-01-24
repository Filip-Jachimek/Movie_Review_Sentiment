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
DATABASE_NAME = 'Reviews'
COLLECTION_NAME = 'Reviews_combined'
CONNECTION_STRING = 'mongodb://localhost:27017/'
CHARS_TO_REPLACE =['?', '!', '.', ',', ':', ';', '"', "'", '(', ')', '[', ']', '{', '}','<br />','-','%','/']



def preprocess_review(review):
    """Return a list or words"""
    for char in CHARS_TO_REPLACE:
        review = review.replace(char, ' ')
    return review.lower().split()

def mongodb_access():
    client = pymongo.MongoClient(CONNECTION_STRING)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    return collection

def count_words(label_filter=None):
    words_count = {}
    client = pymongo.MongoClient(CONNECTION_STRING)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    query = {}
    if label_filter:
        query['label'] = label_filter

    cursor = collection.find(query, {'description': 1})

    for document in cursor:
        content = document.get('description', '')
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


def print_sentiment(sentiment):
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
    """This command create two dictionaries, and saves them as .csv file. Dictionaries are based on comments in database, and created based on amount of words in comments labeled as positive or negative comments"""
    print("I started training myself in positive comments")
    words_count_pos = count_words('positive')
    save_train_result(words_count_pos, POS_DB_FILENAME)
    print("I finished training in positive, now in negativity")
    words_count_neg = count_words('negative')
    save_train_result(words_count_neg, NEG_DB_FILENAME)
    print("I finished all training, now enter comments")

@cli.command()
@click.argument('new_review', type=str)
def report(new_review) -> str:
    """This command create report, which for now, just state sentiment of provided comment negative/positive and exactle sentiment value"""
    words_count_pos = load_train_result(POS_DB_FILENAME)
    words_count_neg = load_train_result(NEG_DB_FILENAME)
    words = preprocess_review(new_review)
    sentiment = compute_sentiment(
        words, words_count_pos, words_count_neg, debug=True)
    print('==')
    print_sentiment(sentiment)


@cli.command()
def merge_command():
    """Merge .txt files from origin folder into single csv_file"""
    merge_to_csv()
    

@cli.command()
def upload_to_mongodb():
    """Upload CSV file to MongoDB."""
    mongodb_access()

    with open(CSV_ALL_REVIEWS_COMBINED, 'r', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        documents = list(csv_reader)

    if documents:
        collection = mongodb_access()
        collection.insert_many(documents)
        click.echo(f'{len(documents)} records uploaded to MongoDB collection: {COLLECTION_NAME}')
    else:
        click.echo('No records found in the CSV file.')

if __name__ == '__main__':
    cli()
