#!/usr/bin/env python3
"""
Lightweight autocorrect for C++ programming prompts
Corrects common typos while preserving technical terms
"""

import sys
from spellchecker import SpellChecker

# Initialize spell checker with custom C++ vocabulary
spell = SpellChecker()

# Add C++ keywords and common terms to prevent overcorrection
cpp_terms = {
    'raii', 'vtable', 'vptr', 'nullptr', 'constexpr', 'decltype',
    'typename', 'variadic', 'sfinae', 'crtp', 'pimpl', 'rvo', 'nrvo',
    'ctor', 'dtor', 'lvalue', 'rvalue', 'xvalue', 'prvalue', 'glvalue',
    'cpp', 'std', 'cout', 'cin', 'endl', 'namespace', 'destructor',
    'polymorphism', 'vtable', 'functor', 'initializer', 'templated',
    'lambda', 'mutex', 'semaphore', 'async', 'bool', 'iostream',
    'fstream', 'stringstream', 'nullptr', 'preprocessor', 'linker',
    'polymorphic', 'metaprogramming', 'tuple', 'variadic', 'smartptr'
}

spell.word_frequency.load_words(cpp_terms)

def autocorrect_prompt(text):
    """
    Corrects typos in user prompt while preserving:
    - C++ keywords and technical terms
    - Code snippets (anything in backticks)
    - Capitalization of proper nouns
    """
    # Don't correct code blocks
    if '`' in text or '```' in text:
        return text

    words = text.split()
    corrected = []

    for word in words:
        # Preserve punctuation
        punctuation = ''
        clean_word = word
        if word and word[-1] in '.,;:?!':
            punctuation = word[-1]
            clean_word = word[:-1]

        # Skip uppercase words (likely acronyms or proper nouns)
        if clean_word.isupper() or clean_word.lower() in cpp_terms:
            corrected.append(word)
            continue

        # Check if word is misspelled
        lower_word = clean_word.lower()
        if lower_word not in spell and len(clean_word) > 2:
            # Get correction
            correction = spell.correction(lower_word)
            if correction and correction != lower_word:
                # Preserve original capitalization
                if clean_word[0].isupper():
                    correction = correction.capitalize()
                corrected.append(correction + punctuation)
            else:
                corrected.append(word)
        else:
            corrected.append(word)

    return ' '.join(corrected)

if __name__ == '__main__':
    # Read from stdin or argument
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
    else:
        text = sys.stdin.read().strip()

    corrected = autocorrect_prompt(text)
    print(corrected, end='')
