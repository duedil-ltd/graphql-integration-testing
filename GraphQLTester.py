#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runs test files in a given dir against the given server."""

import sys
import re
import os
import fnmatch
import requests
import json
import difflib
from inflection import titleize
import os

class GraphQLTester(object):
    regressionUrl = False
    verbose = False
    replace_expectations = False

    """docstring for GraphQLTester"""
    def __init__(self, baseDir, url):
        super(GraphQLTester, self).__init__()
        self.baseDir = baseDir
        self.url = url

    def __call__(self, test):
        return self.runTest(test);

    def extractTestsForSuite(self, suite):
        """Extract all tests in a 'suite' (which must be a directory)."""
        testfilter = False
        if '*' in suite:
            suite, testfilter = suite.split('/', 2)

        if suite[-5:] != '.test':
            try:
                tests = [
                    [suite, t]
                    for t in os.listdir(self.baseDir + suite) if not t.startswith('.') and (not testfilter or fnmatch.fnmatch(t, testfilter))
                ]
            except OSError:
                print('❗ Suite ' + suite + ' does not exist!')
                sys.exit(2)
        else:
            suite, test = suite.split('/')
            tests = [[suite, test]]

        return [suite, tests]

    def runTest(self, test):
        suite, test = test
        test_path = self.baseDir + suite + "/" + test
        query, params, expected = self.getTest(test_path)

        attempts = 0
        response_code = 0
        while response_code != 200 and attempts < 4:
            attempts += 1
            response, response_code = self.runTestQuery(self.url, query, params)

        if response_code != 200:
            print("GraphQL server is having issues with %s. Tried %i times. Returned with %i." % (test, attempts, response_code))

            if self.verbose == 2:
                print("and response: %s" % (response))

            sys.exit(2)

        test_name = titleize(test)[:-5]

        response_split = response.splitlines(1)
        expected_split = expected.splitlines(1)

        if self.checkExpectation(expected_split, response_split):
            print("✅  " + test_name)
        else:
            print("❌ (%i)  %s" % (response_code, test_name))
            if self.verbose == 2 or (self.verbose == 1 and response_code == 200):
                print(''.join(difflib.Differ().compare(expected_split, response_split)))

            if self.replace_expectations:
                self.replaceTest(test_path, response)

        if attempts > 1:
            print("-  ⚠️  it took %i attepts to get a 200 response code for %s" % (attempts, test_name))

    def getTest(self, path):
        """Load the test query and response-assertion JSON from the given path."""
        file_content = open(path, 'r').read()
        test = file_content.split('<===>')

        params = "{}"
        if len(test) == 2:
            query, expected = test
        elif len(test) == 3:
            query, params, expected = test
        else:
            raise ValueError('Test file has to include <===>')

        if self.regressionUrl or expected == 'URL':
            regUrl = self.regressionUrl if self.regressionUrl else expected
            expected, response_code = self.runTestQuery(regUrl, query, params)

            if response_code != 200:
                print("Regression server is having issues. Returned with %i" % (response_code))
                sys.exit(2)
        else:
            # remove any comments as they're not allowed in valid json
            expected = re.sub(r'^\s*?#.+$', '', expected, flags=re.MULTILINE)
            # convert to json and then back into text rule out formatting differences
            expected = json.loads(expected)

            expected = json.dumps(expected, indent=4, sort_keys=True)

        return [query, params, expected]


    def runTestQuery(self, url, query, params):
        """Run the test query and return the server's response."""
        r = requests.post(url, data={'query': query, 'variables': params})

        # convert to json and then back into text rule out formatting differences
        try:
            response = json.loads(r.text)
            return json.dumps(response, indent=4, sort_keys=True), r.status_code
        except:
            return r.text, r.status_code

    def checkExpectation(self, expected, response):
        """Check if the given response matches the given expectation."""
        if len(expected) != len(response):
            return False

        match = True
        for index, line in enumerate(response):
            # Temporarily remove supporting wildcard matching as it unexpectedly also impacted [ and ]
            # if not fnmatch.fnmatch(line, expected[index]):
            if not line == expected[index]:
                match = False

        return match

    def replaceTest(self, path, expected):
        fileContent = open(path, 'r').read()
        test = fileContent.split('<===>')
        test[-1] = "\n"+expected+"\n"

        open(path, 'w').write("<===>".join(test))
