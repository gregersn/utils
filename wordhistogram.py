#!/usr/bin/env python3
import sys
import re
from typing import Dict
from pdfminer.high_level import extract_text


def main():
    words: Dict[str, int] = {}
    text = extract_text(sys.argv[1])
    for word in text.split():
        lower_word = word.lower()
        lower_word = re.sub(r'\W+', '', lower_word)

        if lower_word not in words:
            words[lower_word] = 0

        words[lower_word] += 1
    result_list = sorted(words.items(), key=lambda x: x[0])
    result_list = sorted(result_list, key=lambda x: x[1])
    for word, value in result_list:
        print(word, value)


if __name__ == '__main__':
    main()
