'''
testing it out without any HTTPx client
'''

import urllib.robotparser as rpt

rp = rpt.RobotFileParser()

'''
The problem with the commented rules:- (explained by ChatGPT)

The problem is Python's urllib.robotparser implementation, not your code.

In Python 3.12, RobotFileParser evaluates matching rules in their listed order and 'returns the allowance of the first matching rule'. It does not implement the RFC 9309 longest-match precedence that we expect.

What this means for prod-async-fetcher
This is an important architectural decision. Your project aims to implement RFC 9309 behaviour, so we shouldn't blindly rely on RobotFileParser.can_fetch().

RFC 9309 requires the matching rule with the greatest specificity to take precedence. In this example:

/private/ has 9 characters.

/private/public/ has 16 characters.

Therefore, the Allow rule wins.

My recommendation: Keep RobotFileParser for parsing the robots.txt file, but implement our own rule-matching function that selects the most specific matching rule.

That lets us retain the useful parser functionality without inheriting its matching limitation.
'''
# rp.parse([
#     "User-agent: *",
#     "Disallow: /private/",
#     "Allow: /private/public/",
# ])
# rp.parse([
#     "User-agent: *",
#     "Allow: /private/public/",
#     "Disallow: /private/",
# ])

# print("Python parser test:")
# print(rp.can_fetch("ProdAsyncFetcher/0.1",
#                    "https://example.com/private/"))

# print(rp.can_fetch("ProdAsyncFetcher/0.1",
#                    "https://example.com/private/public/"))

rp.parse([
    "User-agent: *",
    "Disallow: /private/",
    "Allow: /private/public/",
])

rp.modified()

print(rp.can_fetch(
    "ProdAsyncFetcher/0.1",
    "https://example.com/private/"
))

print(rp.can_fetch(
    "ProdAsyncFetcher/0.1",
    "https://example.com/private/public/"
))