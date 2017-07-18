#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runs test files in a given dir against the given server."""

import sys
import getopt
import os
import multiprocessing
import os
import signal
from GraphQLTester import GraphQLTester

DEBUG = False

def printHelp():
    """Print usage instructions."""
    print('Run all suites: tester.py <url>')
    print('Run a suite: tester.py <url> <suite>')
    print('Run multiple suites: tester.py <url> <suite1> <suite2> <suite3>')
    print('Get diff on failure: tester.py -v <url> <suite1>')
    print('Get diff on failure: tester.py --vv <url>')
    print('Test against regression server: tester.py --regression-server="<url>" <url>')
    print('Replace failing tests expectation with the new output: tester.py -r <url>')


def main(argv):
    """Run the tests from command-line arguments."""
    try:
        opts, args = getopt.getopt(argv, "hvrd", ["vv", "regression-server="])
        testsDir = os.getcwd() + '/gqltests/'
        gqlTester = GraphQLTester(testsDir, args[0])
    except getopt.GetoptError:
        print('tester.py -v')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt == '-v':
            gqlTester.verbose = 1
        elif opt == '--vv':
            gqlTester.verbose = 2
        elif opt == '-r':
            gqlTester.replace_expectations = True
        elif opt == '--regression-server':
            gqlTester.regressionUrl = arg
        elif opt == '-d':
            global DEBUG
            DEBUG = True

    if len(args) == 0:
        printHelp()
        sys.exit()

    suites = [suite for suite in os.listdir(testsDir) if os.path.isdir(os.path.join(testsDir, suite))]

    # Get around Pool not gracefully handling KeyboardInterrupt
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    POOL = multiprocessing.Pool(5)
    signal.signal(signal.SIGINT, original_sigint_handler)

    try:
        if len(args) > 1:
            suites = args[1:]

        for suite in suites:
            suite, tests = gqlTester.extractTestsForSuite(suite)

            print("Running " + suite + " test suite")
            print("================================")
            
            if not DEBUG:
                res = POOL.map_async(gqlTester, tests)
                res.get(60 * 5) # Without the timeout this blocking call ignores all signals.
            else:
                for t in tests:
                    gqlTester(t)

    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        POOL.terminate()
        POOL.join()
    else:
        POOL.close()

if __name__ == "__main__":
    main(sys.argv[1:])
