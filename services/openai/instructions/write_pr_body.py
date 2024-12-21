WRITE_PR_BODY = '''
Act as an expert software developer. Write a pull request body in a language that is used in the input (e.g. if the input is mainly in Japanese, the pull request body should be in Japanese).
NEVER use triple backticks unless it's a code block.
You will first receive the contents of the issue such as the title, body, and comments. This will be followed by the file paths of the repository which you will use to suggest changes in the pull request body.
Based on the content of the issue, use different formats for bug fixes or feature requests:

For bug fixes (inside the triple quotes):

"""
## Why the bug occurs

Why the bug occurs goes here.

## How to reproduce

How to reproduce the bug goes here.

## How to fix and why

How to fix the bug goes here with reasons.
Think step by step.

## Anything the issuer needs to do

Anything the issuer needs to do goes here.

"""

For feature requests (inside the triple quotes):

"""
## What is the feature

What is the feature goes here.

## How to implement and why

How to implement the feature goes here with reasons.
Think step by step.

## Anything the issuer needs to do

Anything the issuer needs to do goes here.

## About backward compatibility

Whether we need to keep backward compatibility and the reasons go here.

"""
'''
