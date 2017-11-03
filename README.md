# ISE

### Group Members
| Name          | UNI           |
| ------------- | ------------- |
| Yi Qi	        | yq2211        |
| Xiyan Liu     | xl2672        |

### List of files

* __parser.py__: conduct NLP parsing and tuple retrieving
* __gsearch.py__: call Google searching API and extract text of returned documents
* __main.py__: main logics to run the code
* makefile: initiate the make shortcut
* vm_start.sh: shell file to run all commands in shell
* requirements.txt: all dependencies we need to install
* data.py
* NLPCore.py

### Dependencies and platforms
* Platform: Google Cloud VM, Ubuntu 16.04, **Note that Ubuntu 14.04 is not sufficient to run this program**
* [Stanford CoreNLP software suite](https://stanfordnlp.github.io/CoreNLP/)
    * install [Java 8](http://ubuntuhandbook.org/index.php/2015/01/install-openjdk-8-ubuntu-14-04-12-04-lts/)
    * to download the Stanford CoreNLP jar packages, go to the working directory and run `sudo wget http://nlp.stanford.edu/software/stanford-corenlp-full-2017-06-09.zip`
    * run `unzip stanford-corenlp-full-2017-06-09.zip` to unzip, now there will be a directory named `stanford-corenlp-full-2017-06-09/` under working directory, in the `main()` function, this directory is explicitly specified to run the NLP library
    * since the project is in Python, download `NLPCore.py` and `data.py` from the [Python wrapper of CoreNLP](https://github.com/infobiac/PythonNLPCore) and put them under the working directory
* [__Apache TIKA__](https://github.com/chrismattmann/tika-python)to extract text from webpages
    * install by running `sudo pip install tika`
* __googleapiclient.discovery__, Google Search API
* __argparse__, argument parsing

### Running instructions and Ubuntu deployment

To deploy onto Ubuntu 16.04 VM, on Ubuntu shell:
```sh
$ sudo apt-get update
$ sudo apt-get install git
$ git clone https://github.com/youleer727/ADB_Project2.git
$ cd ADB_Project2
$ bash vm_start.sh
```

To run paradigm "bill gates microsoft" query, simply use makefile

```sh
$ make run
```

This will automatically run paradigm query, you can also customize the query:

```sh
$ python main.py <api> <engine> <relation> <threshold> <query> <tuples>
```

Example:
```sh
$ python main.py AIzaSyAoAvsVDtbehJVan9Pwp_0nI-wWLICamzk 005549065505939013345:yty6lsl3y9y 4 0.35 "bill gates microsoft" 10
```
positional arguments:
  api         Google search API key
  engine      Google search engine ID
  relation    1: Live_In, 2: Located_In, 3: OrgBased_In, 4: Work_For
  threshold   minimal confidence for tuples to be selected, (0, 1]
  query       initial query string, double quoted if there are multiple words
  nr_tuples   number of tuples to be selected

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

* API Key: AIzaSyAoAvsVDtbehJVan9Pwp_0nI-wWLICamzk
* Search engine ID: 005549065505939013345:yty6lsl3y9y
