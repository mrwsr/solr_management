import argparse
import json
import sys

import treq
from twisted.internet import task
from twisted.logger import Logger, globalLogBeginner, jsonFileLogObserver


class HTTPException(Exception):
    pass


class ChunksDocuments(object):
    log = Logger()

    def __init__(self, solrURL):
        self.solrURL = solrURL.rstrip('/')

    def checkResponse(self, response):
        contentDeferred = response.content()
        contentDeferred.addCallback(self.checkStatusAndMaybeFail, response)

    def checkStatusAndMaybeFail(self, content, response):
        if response.code != 200:
            raise HTTPException('{}: {}'.format(response.code, content))

    def add(self, docs, commit=True, timeout=1.0):
        # ugh
        solrURL = self.solrURL
        if commit:
            solrURL += '/update?commit=true'

        responseDeferred = treq.post(
            solrURL,
            json.dumps(docs),
            headers={b'content-type': b'application/json'})
        responseDeferred.addCallback(self.checkResponse)
        responseDeferred.addErrback(self.log.failure)

        return responseDeferred

    def _handleDocChunk(self, _, docChunk, chunksize, *args, **kwargs):
        if not docChunk:
            return
        docsToAdd, docChunk = docChunk[:chunksize], docChunk[chunksize:]
        addedDeferred = self.add(docsToAdd, *args, **kwargs)
        addedDeferred.addCallback(self._handleDocChunk, docChunk, chunksize,
                                  *args, **kwargs)
        return addedDeferred

    def chunkDocs(self, docs, chunksize=500, *args, **kwargs):
        return self._handleDocChunk(
            'ignored', docs, chunksize, *args, **kwargs)


def loopForever(_, chunker, docs):
    chunker.chunkDocs(docs)
    allDocsUploaded = chunker.chunkDocs(docs)
    allDocsUploaded.addCallback(loopForever, chunker, docs)
    return allDocsUploaded


def replay(jsonDocs, solrURL):
    with open(jsonDocs) as f:
        docs = json.load(f)

    chunker = ChunksDocuments(solrURL)
    return loopForever('ignored', chunker, docs)


def main(reactor, *argv):
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('solr_url')
    argument_parser.add_argument('json_docs')

    args = argument_parser.parse_args(argv)

    globalLogBeginner.beginLoggingTo([jsonFileLogObserver(sys.stdout)])

    return replay(args.json_docs, args.solr_url)


task.react(main, sys.argv[1:])
