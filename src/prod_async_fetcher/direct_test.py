'''
testing it out without any HTTPx client
'''

import urllib.robotparser as rpt

rp = rpt.RobotFileParser()

'''
The problem with the commented rules:- (explained by ChatGPT)

The problem is Python's urllib.robotparser implementation, not your code.

In Python 3.12, RobotFileParser evaluates matching rules in their listed order and 'returns the allowance of the first matching rule'. It does not implement the RFC 9309 longest-match precedence that we expect.
'''
# rp.parse([
#     "User-agent: *",
#     "Disallow: /private/",
#     "Allow: /private/public/",
# ])
rp.parse([
    "User-agent: *",
    "Allow: /private/public/",
    "Disallow: /private/",
])

print("Python parser test:")
print(rp.can_fetch("ProdAsyncFetcher/0.1",
                   "https://example.com/private/"))

print(rp.can_fetch("ProdAsyncFetcher/0.1",
                   "https://example.com/private/public/"))