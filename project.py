# 🔴 Projekt update programu:

# $ python project.py
# Enter text: This is awful movie!

import glob


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


def main():
    POS_FILES_FOLDER = "data/aclimdb/train/pos/*.txt"
    NEG_FILES_FOLDER = "data/aclimdb/train/neg/*.txt"

    print("I started training myself in positive comments")
    words_count_pos = count_words(POS_FILES_FOLDER)
    print("I finished training in positive, now in negativity")
    words_count_neg = count_words(NEG_FILES_FOLDER)
    print("I finished all training, now enter comments")
    sentence = input("Enter comment")
    words = preprocess_review(sentence)
    sentiment = compute_sentiment(
        words, words_count_pos, words_count_neg, debug=True)
    print('==')
    print_sentient(sentiment)


if __name__ == "__main__":
    main()
