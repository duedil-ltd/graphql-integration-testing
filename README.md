# GraphQL Integration Testing

Small integration testing utility for GraphQL servers. It was originally a quick hack to check to spec compliance of various servers quickly, but was useful enough to be used for integration testing long term.

It will run your integration tests in parallel.

![GraphQL Compliance Tester Sample Output](https://www.dropbox.com/s/uvhm7usad53i6pa/Screenshot%202016-10-10%2010.49.27.png?dl=1)

## Usage

Run all tests from all suites:

```
gqltester 'http://localhost:8000/'
```

Run a testing suite:

```
gqltester 'http://localhost:8000/' suite-name
```

Run tests matching wildcard search:

```
gqltester 'http://localhost:8000/' suite-name/example\*
```

Run tests and show a diff on failure:

```
gqltester -v 'http://localhost:8000/'
```

Run tests and show a diff on failure but only for HTTP 200:

```
gqltester --vv 'http://localhost:8000/'
```

This is useful if you have your development environment set to 500 on exceptions and show a stack trace. These strack traces will be passive and are generally not desired in `-v`.

Run tests and replace expected responses on failure:

```
gqltester -r 'http://localhost:8000/'
```

This speeds up fixing failures once you've identified they're not regressions.

Run tests and compare against a regression server:

```
gqltester --regression-server='http://prod.acme.com' 'http://localhost:8000/'
```

## Test format

Tests have 3 sections query, variables and expectation. Each section is seperated by `<===>` and variables can be left out of desired.

```
query Example {
	a {
		b
	}
}
<===>
{
	"data": {
		"a": {
			"b": "Expected test value"
		}
	}
}
```

```
query Example($id: String) {
	a {
		b
	}
}
<===>
{
	"id": "1"
}
<===>
{
	"data": {
		"a": {
			"b": "Expected test value"
		}
	}
}
```

You can also put a url as an expectation. This will simply run the query against the url and compare this to the response of the system under test. This is useful for when you have a few tests where the data updates all the time.
It is no different from running gqlteser with the --regression-server option, only that it will do it for that test only.

```
query Example {
	a {
		b
	}
}
<===>
http://staging.acme.com
```

## Installation

```
git clone git@github.com:duedil-ltd/graphql-integration-testing.git
# for mac at least; having a symlink in /usr/local/bin is reasonable. But anyway of adding the script to $PATH will work.
ln -s `PWD`/graphql-integration-testing/bin/graphqltester /usr/local/bin/graphqltester
```

## TODO

- [ ] remove the need to escape *
- [ ] add wildcards for int's
- [ ] allow configuring the number of parallel processes
