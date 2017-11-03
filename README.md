# ISE

### Group UNI

### List of files

* __parser.py__: conduct NLP parsing and tuple retrieving
* __gsearch.py__: call Google searching API and extract text of returned documents
* __main.py__: main logics

### Prerequisites and usage

* Platform: Google Cloud VM, Ubuntu 14.04
* [Stanford CoreNLP software suite](https://stanfordnlp.github.io/CoreNLP/)
    * install [Java 8](http://ubuntuhandbook.org/index.php/2015/01/install-openjdk-8-ubuntu-14-04-12-04-lts/)
    * to download the Stanford CoreNLP jar packages, go to the working directory and run `sudo wget http://nlp.stanford.edu/software/stanford-corenlp-full-2017-06-09.zip`
    * run `unzip stanford-corenlp-full-2017-06-09.zip` to unzip, now there will be a directory named `stanford-corenlp-full-2017-06-09/` under working directory, in the `main()` function, this directory is explicitly specified to run the NLP library
    * since the project is in Python, download `NLPCore.py` and `data.py` from the [Python wrapper of CoreNLP](https://github.com/infobiac/PythonNLPCore) and put them under the working directory
* [__Apache TIKA__](https://github.com/chrismattmann/tika-python)to extract text from webpages
    * install by running `sudo pip install tika`
* __googleapiclient.discovery__, Google Search API
* __argparse__, argument parsing
* Main function help message:

```
$ python main.py -h
usage: main.py [-h] api engine relation threshold query nr_tuples

Iterative Set Expansion

positional arguments:
  api         Google search API key
  engine      Google search engine ID
  relation    1: Live_In, 2: Located_In, 3: OrgBased_In, 4: Work_For
  threshold   minimal confidence for tuples to be selected, (0, 1]
  query       initial query string, double quoted if there are multiple words
  nr_tuples   number of tuples to be selected

optional arguments:
  -h, --help  show this help message and exit
```

### Overall design

* For a specific query, documents returned from Google search API are stored in class `SearchDocument` defined in `gsearch.py`, where text contents are extracted using *Tika* and saved in a member variable
* Relational tuples of each document is extracted using class `NLPParser` defined in `parser.py`, where function `NLPParser.extract_relation()` takes input the document and the type of relationship, and returns all tuples that match the relation (for details see the following section)
* A relational tuple is wrapped in class `RelationTuple` defined in `parser.py`, allowing easy comparison and hashing in order to remove duplications
* The main function receives the tuples of each document, removes duplicates, prunes w.r.t the input threshold, and determines whether the stopping criteria are met

### Detailed design for relational tuple extraction

* For every searched document, the NLP annotator is run twice: 
    * First time without the expensive "parse" and "relation" annotators, simply screening the sentences by their tokens, only save the sentences that contain tokens of that are relevant to the relation, e.g. for relation *Work_In* the sentence must have at least one token of type *PERSON* and one of type *ORGANIZATION*. Besides, the sentences that are too long (>50 tokens) are also discarded, because we found that long sentences seldom produce what we want, but significantly increase the cost of parsing;
    * Second time running with the "parse" and "relation" annotators, since the number of sentences are significantly reduced in the first step, the performance is acceptable. The relational tuples are included in the results *only* if its confidence of the specified type of relation is highest among all types.
* If any one of the tuples returned by a document is new in the output set, include it in the set; otherwise update the one in the set if the confidence has improved for the tuple, but it does not count as a new tuple.

### Keys

* API: 
* Search engine: 
