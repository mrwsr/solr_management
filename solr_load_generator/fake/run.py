import argparse
import os
import json
import pysolr
import sys

from hypothesis import settings


def add_many_documents_at_a_time(solr_connection, generate_documents):
    docs = []
    generate_documents(docs.append)
    solr_connection.add(docs)


def add_one_document_at_a_time(solr_connection, generate_documents):
    generate_documents(lambda doc: solr_connection.add([doc]))


def setup_solr(solr_url, timeout=10):
    return pysolr.Solr(solr_url, timeout=timeout)


def push(args, generate_documents, _setup_solr=setup_solr):
    solr_connection = _setup_solr(args.solr_url)

    if args.fresh or args.clear:
        solr_connection.delete(q='*:*', waitFlush=True)

    if args.clear:
        sys.exit(0)

    if args.bulk:
        add_documents = add_many_documents_at_a_time
    else:
        add_documents = add_one_document_at_a_time

    settings(perform_health_check=False)(generate_documents)

    if args.only is None:
        while True:
            add_documents(solr_connection, generate_documents)
    else:
        add_documents(solr_connection,
                      settings(max_examples=args.only)(generate_documents))


def generate(args, generate_documents):
    if os.path.exists(args.output):
        with open(args.output) as f:
            docs = json.load(f)
    else:
        docs = []

    generate_documents(docs.append)
    with open(args.output, 'w') as f:
        json.dump(docs, f, indent=2)


def main(generate_documents,
         argv=sys.argv[1:],
         _push=push,
         _generate=generate):
    argument_parser = argparse.ArgumentParser()
    subparsers = argument_parser.add_subparsers()

    push = subparsers.add_parser('push')
    push.set_defaults(func=_push)

    push.add_argument('--fresh', '-f',
                                 default=False, action='store_true')
    push.add_argument('--clear', '-c',
                                 default=False, action='store_true')
    push.add_argument(
        '--solr-url', '-s',
        default='http://localhost:8983/solr/gettingstarted')
    push.add_argument('--bulk', '-b',
                      default=False, action='store_true')
    push.add_argument('--only', '-o',
                      default=None,
                      type=int)

    generate = subparsers.add_parser('generate')
    generate.set_defaults(func=_generate)

    generate.add_argument('output')
    generate.add_argument('--only', '-o',
                          default=None,
                          type=int)

    args = argument_parser.parse_args(argv)
    args.func(args, generate_documents)
