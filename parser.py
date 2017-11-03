from NLPCore import NLPCoreClient
from collections import defaultdict

"""Relation Tuple class

a tuple reprsenting a "relation" of interest, in ISE (Iterative Set Expansion) 
we essentailly expand a set of instances of this class
"""
class RelationTuple(object):

    ## the constructor
    #  @param value0(value1) value of tuple elements, type: str
    #  @param type0(type1) type of tuple elements (e.g. PEOPLE), type: str
    #  @param prob probability (confidence) of the tuple, type: float
    #  @param sentence raw sentence that derives the tuple, type: str
    #  @param relation relation of the tuple (e.g. Work_In), type: str
    def __init__(self, value0, value1, type0='', type1='', prob=0.0, sentence='', relation=''):
        self.prob = float(prob)
        self.relation = relation
        self.sentence = sentence.rstrip('\n')
        self.value0, self.type0 = value0.rstrip(), type0.rstrip()
        self.value1, self.type1 = value1.rstrip(), type1.rstrip()
        # let value0 and value1 be lexicographical order to avoid (a,b)&(b,a) duplicates
        if self.value1 > self.value0:
            self.value0, self.value1 = self.value1, self.value0
            self.type0, self.type1 = self.type1, self.type0

    def __hash__(self):
        return hash(self.value0 + self.value1)

    def __eq__(self, other):
        return self.value0 == other.value0 and self.value1 == other.value1

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        return cmp(self.prob, other.prob)

    def __str__(self):
        res = "=============== EXTRACTED RELATION ===============\n"
        res += "Sentence: {}\n".format(self.sentence)
        res += "RelationType: {} | Confidence = {} | ".format(self.relation, self.prob)
        res += "EntityType1 = {} | EntityValue1 = {} | ".format(self.type0, self.value0)
        res += "EntityType2 = {} | EntityValue2 = {}\n".format(self.type1, self.value1)
        res += "============== END OF RELATION DESC =============="
        return res

"""NLP Parser class

wrapper (of wrapper) of the Stanford NLP tools, to analyze the text of the 
webpages and extract tuples of target relation
"""
class NLPParser(object):
    
    ## the constructor
    #  @param lib the root path of Stanford NLP tools, type: str
    def __init__(self, lib):
        self.client = NLPCoreClient(lib)
        # some default parameters to feed the "annotator"
        self.annotators = "tokenize,ssplit,pos,lemma,ner,parse,relation"
        self.parsemodel = "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz"
        self.useSUTime = "0"
        # used for filtering sentences that contain certain named entities like 'PERSON'
        # e.g. if relation is 'Work_In' then there must be at least one entity of 'PERSON' 
        # and one of 'ORGANIZATION' in the sentence
        self.entity_filters = {
            "Live_In": lambda x : x['PERSON']>0 and x['LOCATION']>0,
            "Located_In": lambda x : x['LOCATION']>1,
            "OrgBased_In": lambda x : x['LOCATION']>0 and x['ORGANIZATION']>0,
            "Work_For": lambda x : x['PERSON']>0 and x['ORGANIZATION']>0
        }

    ## calling the annotator
    #  @param lines texts to process, type: list(str)
    #  @param annotators specific annotators, type: str
    #  @param chunk size of chunk to process in one batch, type: int
    #  
    #  @ret list of data.Sentence instances, each representing a parsed sentence
    def annotate(self, lines, annotators=None, chunk=1e6):
        if not annotators:
            annotators = self.annotators
        properties = {
            "annotators": annotators,
            "parse.model": self.parsemodel,
            "ner.useSUTime": self.useSUTime
        }

        # split the processing into chunck to avoid memory overflowing, 
        # or generating gigantic temp files (like the input.txt.html)
        # it might not be necessary so I leave the options here
        sentences = []
        i = 0
        chunk = int(chunk)
        while i < len(lines):
            j = min(len(lines), i + chunk)
            if i >= j:
                break
            # calling annotator, a Python-wrapped Java codes
            document = self.client.annotate(text=lines[i:j], properties=properties)
            sentences.extend(document.sentences)
            i = j
        return sentences

    ## first round of parsing, screening sentences with relevant named entities
    #  @param key key to the document, for caching, type: str
    #  @param lines texts to process, type: list(str)
    #  @param relation relation of interest (e.g. Work_In), type: str
    #  
    #  @ret list of sentences in pure text
    def __first_round(self, key, lines, relation):
        res = []
        if not relation in self.entity_filters:
            return res
        entity_filter = self.entity_filters[relation]

        # calling a selection of annotators (no parsing or relation)
        sentences = self.annotate(lines, "tokenize,ssplit,pos,lemma,ner")

        for sentence in sentences:
            if len(sentence.tokens) >= 50:
                ##
                # sometimes the scrapper returns very long sentences that are  
                # very computational expensive but usually not as productive in 
                # generating relation tuples, the sentence length limit of 50 
                # words comes after several experiments on the trade-off of 
                # performance and correctness
                continue

            # count number of named entities and filter sentences accordingly
            entity_counts = defaultdict(int)
            for token in sentence.tokens:
                entity_counts[token.ner] += 1
            # filter by named entity counts 
            if entity_filter(entity_counts):
                line = u' '.join([token.word for token in sentence.tokens]).encode('ascii', 'ignore').replace('|', '')
                res.append(line)
        return res

    ## second round of parsing, get the relations
    #  @param key key to the document, for caching, type: str
    #  @param lines texts to process, type: list(str)
    #  @param relation relation of interest (e.g. Work_In), type: str
    #  
    #  @ret list of relation descriptions (entity#1 value, entity#2 value, 
    #       entity#1 type, entity#2 type, confidence, sentence text), type: tuple
    def __second_round(self, key, lines, relation):
        # calling a full set of annotators (default)
        sentences = self.annotate(lines)

        res = []
        for sentence in sentences:
            raw = "" # raw text of the sentence
            for rel in sentence.relations:
                # each pair of relation in the sentence contains a relation type, 
                # its probability (confidence), and a pair of entities with value and type.
                # skip the relationship pair if the confidence of the relation we are looking 
                # for is not the highest among all relations
                probabilities = rel.probabilities
                if float(probabilities.get(relation, -1)) < max(map(float, probabilities.values())):
                    continue

                e = rel.entities
                if len(e) == 2:
                    if not raw:
                        # construct the raw text of sentence now by 
                        # joining the "word"s of its tokens
                        raw = u' '.join([t.word for t in sentence.tokens]).encode('ascii', 'ignore')
                    # append the relation description as a tuple to the results
                    res.append((e[0].value.rstrip(), e[1].value.rstrip(), \
                        e[0].type.rstrip(), e[1].type.rstrip(), \
                        probabilities[relation], raw))
        return res

    ## extract relation tuples from a search document
    #  @param doc the search document with scraped text, type: SearchDocument
    #  @param relation relation of interest (e.g. Work_In), type: str
    #  
    #  @ret list of relation tuples, type: list(RelationTuple)
    def extract_relation(self, doc, relation):
        key = doc.key

        # first round, screen sentences
        lines = self.__first_round(key, doc.text.split('\n'), relation)
        
        # second round, get relations
        relations = self.__second_round(key, lines, relation)

        # combine relation tuples with same entities
        res = {}
        for t in relations:
            (v0, v1, t0, t1, prob, sentence) = t
            rt = RelationTuple(v0, v1, t0, t1, prob, sentence, relation)
            key = hash(rt)
            if not key in res or res[key] < rt:
                # new tuple or better than existing, add to results
                res[key] = rt
        return res.values()
