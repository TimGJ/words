# Simplistic Makefile

# Clean generated files out

.PHONY: clean
clean:
	rm  -rvf *.txt *.pyc *.json data/*

# Generate data/words.txt from the aspell dictionaries

.PHONY: words
words:
	$(MAKE) data/words.txt

data/words.txt:
	aspell -d en_GB dump master | aspell -l en expand > data/words.txt;

# Generate the consolidated word list (text format) from combining and filtering the input lists

.PHONY: consolidated
consolidated:
	$(MAKE) data/consolidated.txt

data/consolidated.txt: data/words.txt src/CreateConsolidatedWordList.py
	python3 src/CreateConsolidatedWordList.py --infile data/words.txt --infile /usr/share/english-words/words.txt --outfile data/consolidated.txt

.PHONY: analysed
analysed:
	$(MAKE) data/analysed.json

data/analysed.json: consolidated
	python3 src/AnalyzeConsolidaedWordList.py --workers 24 data/consolidated.txt data/analysed.json
