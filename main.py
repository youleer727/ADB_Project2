#!/usr/bin/env python

import argparse
from gsearch import *
from parser import *
from collections import defaultdict
import os
import sys

STANFORD_NLP_PATH = os.path.abspath(os.path.dirname(__file__)) + '/../' + 'stanford-corenlp-full-2017-06-09'

## validate input arguments
def validate(args):
    # validate search API
    api = args.api
    if not api:
        try:
            from secrets import GSEARCH_JSON_API
            api = GSEARCH_JSON_API
        except:
            raise ValueError("[ERROR] Search API not specified")
    # validate search engine
    engine = args.engine
    if not engine:
        try:
            from secrets import GSEARCH_ENGINE
            engine = GSEARCH_ENGINE
        except:
            raise ValueError("[ERROR] Search engine ID not specified")
    # validate relation
    relations = {1:'Live_In', 2: 'Located_In', 3: 'OrgBased_In', 4: 'Work_For'}
    if not args.relation in relations:
        raise ValueError("[ERROR] invalid relation")
    relation = relations[args.relation]
    # validate threshold
    threshold = args.threshold
    if not 0 < threshold <= 1.0:
        raise ValueError("[ERROR] threshold {} not in range (0, 1]".format(
            threshold))
    # validate nr_tuples
    nr_tuples = args.nr_tuples
    if nr_tuples <= 0:
        raise ValueError("[ERROR] invalid number of tuples {}".format(nr_tuples))
    # validate query
    query_terms = [unicode(i) for i in args.query.strip().split(' ')]
    if not query_terms:
        raise ValueError("[ERROR] empty/invalid query string")

    # all set, return validated arguments
    return api, engine, relation, threshold, nr_tuples, query_terms


## main
def main(args):
    global STANFORD_NLP_PATH
    api, engine, relation, threshold, nr_tuples, query_terms = validate(args)

    print "\nParameters:"
    print "Client key      = " + api
    print "Engine key      = " + engine
    print "Relation        = " + relation
    print "Threshold       = " + str(threshold)
    print "Query           = " + " ".join(query_terms)
    print "# of Tuples     = " + str(nr_tuples)

    # set of output tuples
    tuples = {} # key:hash of RelationTuple instance, value: RelationTuple instance
    # set of tuples used as query terms
    queries = set()
    # set of documents processed
    processed = set()
    # NLP parser
    nlplib = STANFORD_NLP_PATH
    parser = NLPParser(nlplib)

    iteration, maxit = 1, 10
    while True:
        query = " ".join(query_terms)
        print "=========== Iteration: {} - Query: {} ===========".format(
            iteration, query)

        # search Google
        docs = gsearch(query, api, engine)
        queries.add(tuple(query_terms))

        # process each document of Google search results
        new_tuples_found = False
        for i, doc in enumerate(docs, 1):
            print "[{}] Processing: {}".format(i, doc.url)
            if doc.key in processed:
                # no need to process if already processed
                print "Already processed, skipping..."
                continue
            processed.add(doc.key)
            
            count = 0
            for rt in parser.extract_relation(doc, relation):
                # rt is a RelationTuple class instance
                key = hash(rt)
                if not key in tuples:
                    # new tuple for ISE
                    new_tuples_found = True
                    tuples[key] = rt
                    count += 1
                    print rt
                elif tuples[key] < rt:
                    # existing tuple, but this one has better confidence, update it
                    tuples[key] = rt
            print "Relations extracted from this website: {} (Overall: {})".format(
                count, len(tuples))

        print "Pruning relations below threshold..."
        pruned = sorted(filter(lambda x:x.prob >= threshold, tuples.values()), reverse=True)

        print "Number of tuples after pruning: {}".format(len(pruned))
        print "================== ALL RELATIONS ================="
        for rt in pruned:
            line = "Relation Type: %s | Confidence: %.3f |" % (relation, rt.prob)
            line += " Entity #1: {} ({})\t|".format(rt.value0, rt.type0)
            line += " Entity #2: {} ({})".format(rt.value1, rt.type1)
            print line
        
        if not new_tuples_found:
            print "No new tuples found. Shutting down..."
            break

        if len(pruned) >= nr_tuples:
            print "Program reached {} number of tuples. Shutting down...".format(len(pruned))
            break
        
        if iteration > maxit:
            print "Maximum iterations reached. Shutting down..."
            break
        iteration += 1
        
        # new query terms for next iteration, derived from the tuple with 
        # highest confidence and has not yet been used as query terms
        query_terms, best = [], 0.0
        for rt in tuples.values():
            q = (rt.value0, rt.value1)
            if not q in queries and rt.prob > best:
                query_terms, best = q, rt.prob
    # end of main()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Iterative Set Expansion')
    parser.add_argument('api', type=str, help='Google search API key')
    parser.add_argument('engine', type=str, help='Google search engine ID')
    parser.add_argument('relation', type=int, help='1: Live_In, 2: Located_In, 3: OrgBased_In, 4: Work_For')
    parser.add_argument('threshold', type=float, help='minimal confidence for tuples to be selected, (0, 1]')
    parser.add_argument('query', type=str, help='initial query string, double quoted if there are multiple words')
    parser.add_argument('nr_tuples', type=int, help='number of tuples to be selected')

    # args = vars()
    main(parser.parse_args())
