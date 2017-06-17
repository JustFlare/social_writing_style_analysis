import csv
import json
import re
import string
import os

from nltk.tokenize import sent_tokenize, wordpunct_tokenize
from collections import defaultdict

DATA_DIR = 'data'
ANALYSIS_DIR = 'analysis'

READ_PREPROCESSED = False
AVG = False
COMMENT_PER_USER_THRESHOLD = 10

YEAR_FROM = 1957
YEAR_TO = 2010

REFERENCE = re.compile('^\[id\d+\|\w+\],', re.U)
HTML_TAG = re.compile('</?\w+[^>]*>', re.U)
HASH_TAG = re.compile('(\s|^)#\w+', re.U)
LINK = re.compile('(https?://)?(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)', re.U)
ESCAPED_SYMBOLS = re.compile('&\w+;', re.U)
SQUASH_SPACE = re.compile('\s{2,}', re.U)
SQUASH_PUNCT = re.compile(r"""([%s])\1+""" % string.punctuation, re.U)

POSITIVE_SMILEY = [':-)', ':)', ':D', ':o)', ':]', ':3', ':c)', ':>', '=]', '8)', '=)', ':}', ':^)', ':?)', '?', ':-D',
                   '8-D', '8D', 'x-D', 'xD', 'XD', '=3', 'B^D', ':-))', ':*', ':^*', ')+', ';-)', ';)', '*-)', '*)',
                   ';-]', ';]', ';D', ':-P', ':P', 'xp', 'XP', ':-p', ':p', '=p']
NEGATIVE_SMILEY = ['>:[', ':-(', ':(', ':-c', ':c', ':<', ':-[', ':[', ':{', ';(', ':@', '>:(', ':\'-(', ':\'(', 'D:',
                   'D8', 'D;', ':-.', ':/', ':\\', '=/', '=\\', ':L', '=L', ':S', '>.<']
NEUTRAL_SMILEY = ['>:O', ':-O', ':O', 'O_O', 'o-o', 'O_o', 'o_O', 'o_o', 'O-O', 'Oo', 'Оо', 'оО', 'О_о', ':|', ' :-|',
                  '<3', '%-)', ' %)', ':-&', ':&']

SMILEYS = set(POSITIVE_SMILEY + NEGATIVE_SMILEY + NEUTRAL_SMILEY)


def preprocess_comment(text, squash_punct=True):
    text = SQUASH_SPACE.sub(' ', ESCAPED_SYMBOLS.sub('', HASH_TAG.sub('', HTML_TAG.sub('', LINK.sub('', REFERENCE.sub('', text))))))
    text = SQUASH_PUNCT.sub(r'\1', text) if squash_punct else text
    text = text.strip()

    # remove smileys
    text = ' '.join([token for token in text.split(' ') if token not in SMILEYS])

    if not text:
        return None

    char_cnt = len(text)
    sent_cnt = word_cnt = punct_cnt = word_len = 0

    for s in sent_tokenize(text.strip()):
        sent_cnt += 1
        for token in wordpunct_tokenize(s.strip()):
            if token in string.punctuation:
                punct_cnt += 1
            else:
                word_cnt += 1
                word_len += len(token)

    return {
        'sent_cnt': sent_cnt,
        'char_cnt': char_cnt,
        'char_cnt_sent': float(char_cnt) / sent_cnt,
        'word_cnt': word_cnt,
        'word_cnt_sent': float(word_cnt) / sent_cnt,
        'word_len_avg': (float(word_len) / word_cnt) if word_cnt else 0,
        'punct_cnt': punct_cnt,
        'punct_cnt_sent': float(punct_cnt) / sent_cnt,
        'punct_cnt_word': (float(punct_cnt) / word_cnt) if word_cnt else 0,
        'punct_cnt_char': float(punct_cnt) / char_cnt
    }


def preprocess_user(u):
    if 'bdate' not in u or u['bdate'].count('.') != 2:
        return None

    u['year'] = int(u['bdate'].split('.')[-1])
    if not YEAR_FROM <= u['year'] <= YEAR_TO:
        return None
    del u['bdate']

    if 'first_name' in u:
        del u['first_name']
    if 'last_name' in u:
        del u['last_name']

    return u


if __name__ == '__main__':
    if READ_PREPROCESSED:
        with open('%spreprocessed_data.json' % ('avg_' if AVG else '')) as data_json:
            total_data = json.load(data_json)
    else:
        total_data = []
        by_comments_count = defaultdict(int)

        for filename in os.listdir(DATA_DIR):
            with open(os.path.join(DATA_DIR, filename), encoding='utf-8') as data_json:
                print("Processing %s" % filename)
                data = json.load(data_json)

                for user_id, user in data['users'].items():
                    data['users'][user_id] = preprocess_user(user)

                print("Users processed. Start retrieving comments features...")
                for user_id, comments in data['data'].items():
                    if not data['users'][user_id] or len(comments) < COMMENT_PER_USER_THRESHOLD:
                        continue

                    features = []
                    for comment in comments:
                        f = preprocess_comment(comment)
                        if not f:
                            continue
                        features.append(f)

                    if len(features) < COMMENT_PER_USER_THRESHOLD:
                        continue

                    comments_cnt = len(features)
                    by_comments_count[comments_cnt] += 1

                    if AVG:
                        # calculate features avg values
                        total = features[0]
                        for key in total.keys():
                            for f in features[1:]:
                                total[key] += f[key]
                            total[key] /= comments_cnt
                        total_data.append((data['users'][user_id], total))
                    else:
                        # proceed (user_data, comment_features) pairs
                        for f in features:
                            total_data.append((data['users'][user_id], f))

        with open('%spreprocessed_data.json' % ('avg_' if AVG else ''), mode='w') as out:
            json.dump(total_data, out)

        with open(os.path.join(ANALYSIS_DIR, 'by_comments_count.csv'), mode='w') as out:
            writer = csv.writer(out)
            for cnt in sorted(by_comments_count.keys()):
                writer.writerow((cnt, by_comments_count[cnt]))

    if AVG:
        # calculate birth year stats only within average data
        by_birth_year = defaultdict(int)
        for item in total_data:
            user, features = item
            by_birth_year[user['year']] += 1

        with open(os.path.join(ANALYSIS_DIR, 'by_birth_year.csv'), mode='w') as out:
            writer = csv.writer(out)
            for year in range(YEAR_FROM, YEAR_TO + 1):
                writer.writerow((year, by_birth_year[year]))
