#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runs test files in a given dir against the given server."""

import click
import sys
import getopt
import os
import multiprocessing
import os
import signal
from GraphQLTester import GraphQLTester

DEBUG = False

@click.command()
@click.argument('url')
@click.argument('suite', nargs=-1)
@click.option('-v', is_flag=True, help='Log out diffs on failure for HTTP 200 responses.')
@click.option('-vv', is_flag=True, help='Log out diffs on failure for HTTP 200 responses as well as error responses for non HTTP 200 responses.')
@click.option('-d', is_flag=True, help='Disable running tests in parallel. This improves error messages.')
@click.option('-r', is_flag=True, help='Replace failed test expectations with new observed responses.')
@click.option('--regression-server', default="", help='Disable running tests in parallel. This improves error messages.')
def main(url, suite, v, vv, d, r, regression_server):
    """Integration testing utility for GraphQL servers.

    Runs tests located in the ./gqltests folder.

    Use the suite argument to narrow down which tests to run.

    SUITE=feature_x will run any tests inside gqltests/feature_x

    SUITE=feature_x/file_y will run a single test in gqltests/feature_x/file_y

    SUITE=feature_x/file\* will run any test in gqltests/feature_x matching file*
    """

    testsDir = os.getcwd() + '/gqltests/'
    gqlTester = GraphQLTester(testsDir, url)

    if v:
        gqlTester.verbose = 1
    if vv:
        gqlTester.verbose = 2
    if r:
        gqlTester.replace_expectations = True
    if regression_server:
        gqlTester.regressionUrl = regression_server
    if d:
        global DEBUG
        DEBUG = True

    # Get around Pool not gracefully handling KeyboardInterrupt
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    POOL = multiprocessing.Pool(5)
    signal.signal(signal.SIGINT, original_sigint_handler)

    test_results = []
    try:
        # suite is in fact an array of suites
        if len(suite):
            suites = suite
        else:
            suites = [suite for suite in os.listdir(testsDir) if os.path.isdir(os.path.join(testsDir, suite))]

        for suite in suites:
            suite, tests = gqlTester.extractTestsForSuite(suite)

            click.echo("Running " + suite + " test suite")
            click.echo("================================")
            
            if not DEBUG:
                res = POOL.map_async(gqlTester, tests)
                test_results = test_results + res.get(60 * 5) # Without the timeout this blocking call ignores all signals.
            else:
                for t in tests:
                    test_results.append(gqlTester(t))

    except KeyboardInterrupt:
        click.echo("Caught KeyboardInterrupt, terminating workers")
        POOL.terminate()
        POOL.join()
    except multiprocessing.TimeoutError:
        click.echo("Process timed out")

    POOL.terminate()
    POOL.close()

    click.echo("Total tests run: %d. Failed tests: %d" % (len(test_results), len([x for x in test_results if x is False])))

    # If there was a failure: exit with an error code to allow CI to pick it up.
    if (False in test_results):
        exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])
