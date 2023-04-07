"""
Takes a list of words and for each word in the list computes how many letters it has in common with
all the other words. For each word it counts how many matching letters it has in the correct place
and how many letters are correct but in the wrong place.

So STARE has one letter in the correct position and two additional letters which match but are in the wrong
position when checked against REACH.

This operation is O(n**2), and n is relatively large (> 10**4), so for reasons of efficiency the task will
be divided into a number of chunks to be executed concurrently.
"""
import argparse
import collections
import concurrent.futures
import json
import logging
import time


class WordScore:
    """
    For a particular word computes the match statistics with the rest of the corpus.
    """

    def __init__(self, candidate, corpus):
        self.word = candidate
        self.position = 0
        self.present = 0
        for word in corpus:
            leftw = collections.defaultdict(int)
            leftc = collections.defaultdict(int)
            for index in range(len(candidate)):
                if word[index] == candidate[index]:
                    self.position += 1
                else:
                    leftw[word[index]] += 1
                    leftc[candidate[index]] += 1
            for letter, count in leftc.items():
                try:
                    self.present += min(count, leftw[letter])
                except KeyError:
                    pass
    def __repr__(self):
        return f'{self.word}: {self.position} {self.present}'

    def asDict(self):
        """
        Return as a dictionary for subsequent serialisation as e.g. JSON
        """
        return {"word": self.word, "present": self.present, "position": self.position}
def ScoreChunk(corpus, chunkid, start, end):
    """
    Computes the scores of a chunk of words.
    """
    logging.info(f'Starting ScoreChunk #{chunkid} {start}..{end}')
    results = []
    for index, word in enumerate(corpus[start:end]):
        logging.debug(f'{chunkid}/{index} {word}')
        results.append(WordScore(word, corpus))
    logging.info(f'Finishing ScoreChunk #{chunkid} {start}..{end}')
    return results

class CorpusScore:
    """
    Computes the scores for a corpus of words
    """

    def __init__(self, corpus, **kwargs):

        self.workers = kwargs.get('workers', 10)  # Number of worker processes
        self.corpus = corpus
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures = [executor.submit(ScoreChunk, self.corpus, i, start, end)
                       for i, (start, end) in enumerate([b for b in self.chunkBoundaries()])]
            self.result = [word for future in concurrent.futures.as_completed(futures) for word in future.result()]

    def chunkBoundaries(self):
        chunkSize = round(len(self.corpus) / self.workers)
        for offset in range(0, len(self.corpus), chunkSize):
            yield offset, min(offset+chunkSize-1, len(self.corpus)-1)

    def writeOutput(self, outfile):
        """
        Writes the results to a JSON file for downstream scoring
        """
        payload = [r.asDict() for r in self.result]
        with open(outfile, "w") as out:
            json.dump(payload, out, indent=2)
        logging.info(f'Written output to {outfile}')
        

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Analyse words')
    ap.add_argument('--debug', help='Debug mode', action='store_true')
    ap.add_argument('--workers', help='Number of workers', type=int)
    ap.add_argument('--max-words', help="Limit size of corpus", type=int)
    ap.add_argument('input', help='Corpus of words (txt file)')
    ap.add_argument('output', help='Destination (json file)')
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s')
    try:
        words = open(args.input).read().splitlines()
    except FileNotFoundError as e:
        print(f"Couldn't open corpus file {args.input}: {e}")
    else:
        logging.info(f'Read {len(words):,} words from {args.input}')
        if args.max_words:
            logging.info(f'Truncating corpus to {args.max_words:,} words')
            words = words[:args.max_words]
        cs = CorpusScore(words, workers=args.workers)
        cs.writeOutput(args.output)
