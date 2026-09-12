# Security

This library reads text files and downloads data tables from Hugging Face. It runs no network
service and executes nothing from the data it loads.

## Reporting a problem

Please report vulnerabilities privately through GitHub's "Report a vulnerability" button on the
Security tab of this repository, rather than in a public issue. You can expect an acknowledgement
within a week.

## What counts

- A crafted input file that causes code execution, or reads or writes outside the process.
- Anything that makes the library fetch or run code from somewhere other than the declared dataset.

Wrong stress, a missed rhyme or a false agreement error is a bug, not a vulnerability — please open
a normal issue for those, ideally with the word or line that was judged wrongly.
