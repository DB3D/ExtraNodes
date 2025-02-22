# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

import re


def match_exact_tokens(string:str, tokenlist:list) -> list:
    """
    Get a list of matching token, if any token in our token list match in our string list

    A token is matched exactly:
      - For numbers (integer/float), it won't match if the token is part of a larger number.
      - For alphabetic tokens, word boundaries are used.
    """
    def build_token_pattern(tokens):
        def boundary(token):
            # For numbers, ensure the token isn't part of a larger number.
            if re.fullmatch(r'\d+(?:\.\d+)?', token):
                return r'(?<![\d.])' + re.escape(token) + r'(?![\d.])'
            else:
                # For alphabetic tokens, use word boundaries.
                return r'\b' + re.escape(token) + r'\b'
        return '|'.join(boundary(token) for token in tokens)
    
    pattern = build_token_pattern(tokenlist)
    return re.findall(pattern, string)


def replace_exact_tokens(string:str, tokens_mapping:dict) -> str:
    """Replace any token in the given string with new values as defined by the tokens_mapping dictionary."""
    
    def build_token_pattern(tokens):
        def boundary(token):
            # If token is a number (integer or float)
            if re.fullmatch(r'\d+(?:\.\d+)?', token):
                # Use negative lookbehind and lookahead to ensure the token isn't part of a larger number.
                return r'(?<![\d.])' + re.escape(token) + r'(?![\d.])'
            else:
                # For alphabetic tokens, use word boundaries.
                return r'\b' + re.escape(token) + r'\b'
        # Build the overall pattern by joining each token pattern with '|'
        return '|'.join(boundary(token) for token in tokens)

    pattern = build_token_pattern(tokens_mapping.keys())
    
    def repl(match):
        token = match.group(0)
        return tokens_mapping.get(token, token)
    
    return re.sub(pattern, repl, string)