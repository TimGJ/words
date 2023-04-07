"""
Class(es) to represent lists of words.
"""
import itertools
import re
import argparse
import logging
import json

class WordList:

    def __init__(self, filename):
        self.filename = filename
        self.pattern = re.compile(r'^[a-z]{5}$')
        self.words = [word for word in open(self.filename).read().splitlines() if self.pattern.match(word)]
        logging.debug(f'Created wordlist from {filename}: {len(self.words):,} words')

    def __repr__(self):
        return f'{self.filename}: {len(self.words):,} words'


class ConsolidatedWordList:
    """
    A collection of various lists of words which are filtered, compared and consolidated and ultimately
    written.
    """
    def __init__(self, **kwargs):
        self.wordlists = []
        self.consolidated = []

    def __repr__(self):
        return f'{len(self.wordlists):,} lists {len(self.consolidated):,} words'

    def addWordList(self, filename):
        """
        Reads
        :param filename:
        :return: None
        """
        logging.debug(f'Adding {filename}')
        self.wordlists.append(WordList(filename))

    def consolidate(self):
        c = {word for wordlist in self.wordlists for word in wordlist.words}
        self.consolidated = sorted(list(c))
        logging.debug(f'Consolidated list contains {len(self.consolidated):,} words from {self.consolidated[0]} to {self.consolidated[-1]}')

    def write(self, filename):
        logging.debug(f'Writing output to {filename}')
        with open(filename, 'w') as outfile:
            outfile.write('\n'.join(self.consolidated))

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Process word lists')
    ap.add_argument('--debug', '-d', help='Debug mode', action='store_true')
    ap.add_argument('--infile', help='Input word list', action='append')
    ap.add_argument('--outfile', help='Output consolidated wordlist')
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s')
    if not args.infile:
        ap.error("No input files specified")

    cwl = ConsolidatedWordList()
    for infile in args.infile:
        try:
            cwl.addWordList(infile)
        except FileNotFoundError as e:
            logging.error(f'Error processing {infile}: {e}')
    cwl.consolidate()
    try:
        cwl.write(args.outfile)
    except PermissionError as e:
        logging.error(f'Error writing {args.outfile}: {e}')
    else:
        logging.info(f'Written {args.outfile}')

