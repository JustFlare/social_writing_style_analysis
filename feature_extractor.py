import json
import re
import string
import os

from nltk.tokenize import sent_tokenize, wordpunct_tokenize

DATA_DIR = 'bdate_data'

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

    return text, {
        'sent_cnt': sent_cnt,
        'char_cnt': char_cnt,
        'char_cnt_sent': float(char_cnt) / sent_cnt,
        'word_cnt': word_cnt,
        'word_cnt_sent': float(word_cnt) / sent_cnt,
        'word_len_avg': float(word_len) / word_cnt,
        'punct_cnt': punct_cnt,
        'punct_cnt_sent': float(punct_cnt) / sent_cnt,
        'punct_cnt_word': float(punct_cnt) / word_cnt,
        'punct_cnt_char': float(punct_cnt) / char_cnt
    }


if __name__ == '__main__':
    for f in os.listdir(DATA_DIR):
        with open(os.path.join(DATA_DIR, f), encoding='utf-8') as f_json:
            data = json.load(f_json)
            for _, comments in data.items():
                for c in comments:
                    c = c.strip()
                    if len(c) == 1:
                        continue

                    c, features = preprocess_comment(c)
                    pass
