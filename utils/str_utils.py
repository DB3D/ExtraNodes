# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

import re

from .. import get_addon_prefs



def is_float_compatible(string):
    """ check if a string can be converted to a float value"""

    assert type(string) is str
    if (string[0]=='.'):
        return False
    try:
        float(string)
        return True
    except (ValueError, TypeError):
        return False


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


def word_wrap(string="", layout=None, alignment="CENTER", max_char=70, char_auto_sidepadding=1.0, context=None, active=False, alert=False, icon=None, scale_y=1.0,):
    """word wrap a piece of string on a ui layout""" 
    
    if ((max_char=='auto') and (context is not None)):
        
        charw = 6.0 # pixel width of a single char
        adjst = 35 # adjustment required
        totpixw = context.region.width * char_auto_sidepadding
        uifac = context.preferences.system.ui_scale
        max_char = ((totpixw/uifac)-adjst)/charw
    
    #adjust user preferences
    sett_plugin = get_addon_prefs()
    max_char = int(max_char * sett_plugin.ui_word_wrap_max_char_factor)
    scale_y = sett_plugin.ui_word_wrap_y * scale_y
    
    def wrap(string,max_char):
        """word wrap function""" 

        original_string = string
        newstring = ""
        
        while (len(string) > max_char):

            # find position of nearest whitespace char to the left of "width"
            marker = max_char - 1
            while (marker >= 0 and not string[marker].isspace()):
                marker = marker - 1

            # If no space was found, just split at max_char
            if (marker==-1):
                marker = max_char
    
            # remove line from original string and add it to the new string
            newline = string[0:marker] + "\n"
            newstring = newstring + newline
            string = string[marker + 1:]

        return newstring + string

    #Multiline string? 
    if ("\n" in string):
          wrapped = "\n".join([wrap(l,max_char) for l in string.split("\n")])
    else: wrapped = wrap(string,max_char)

    #UI Layout Draw? 
    if (layout is not None):

        lbl = layout.column()
        lbl.active = active 
        lbl.alert = alert
        lbl.scale_y = scale_y

        for i,l in enumerate(wrapped.split("\n")):

            if (alignment):
                  line = lbl.row()
                  line.alignment = alignment
            else: line = lbl

            if (icon and (i==0)):
                line.label(text=l, icon=icon)    
                continue

            line.label(text=l)
            continue 
    
    return wrapped
    