import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
from textblob import TextBlob
import re
from collections import Counter
from functools import lru_cache
from tqdm import tqdm  # for progress bar
from nltk.tokenize import regexp_tokenize
from textblob import Word
from textblob.en import spelling as _spelling

# TextBlob.correct() splits text into these tokens and corrects each one
# (textblob/blob.py, BaseBlob.correct).
_BLOB_TOKEN = r"\w+|[^\w\s]|\s"
_PUNCTUATION = ".,;:!?()[]{}`''\"@#$^&*+-|=~_"  # textblob/_text.py PUNCTUATION


def _misspelled_reference(word):
    """The original check: TextBlob's full spelling correction of the word."""
    return str(TextBlob(word).correct()) != word


@lru_cache(maxsize=200000)
def _token_corrected(token):
    return str(Word(token).correct()) != token


_KNOWN = None


def _known_words():
    global _KNOWN
    if _KNOWN is None:
        if len(_spelling) == 0:
            _spelling.load()
        _KNOWN = frozenset(dict.keys(_spelling))
    return _KNOWN


def _has_correction_reference(token):
    """Edit-distance-2 existence by brute force (TextBlob's _edit1 applied twice).
    Kept to check the fast version against; ~250k lookups for an unknown token."""
    known = _known_words()
    e1 = _spelling._edit1(token)
    if any(w in known for w in e1):
        return True
    return any(w in known for a in e1 for w in _spelling._edit1(a))


_DELETES = None  # (any single deletion of a dictionary word, {(position, deletion)})


def _delete_index():
    """One-character deletions of every dictionary word, plain and keyed by position."""
    global _DELETES
    if _DELETES is None:
        plain, positional = set(), set()
        for w in _known_words():
            for i in range(len(w)):
                d = w[:i] + w[i + 1:]
                plain.add(d)
                positional.add(f"{i}\x00{d}")
        _DELETES = (frozenset(plain), frozenset(positional))
    return _DELETES


def _known_within_one_edit(e):
    """Is some dictionary word reachable from e by one of TextBlob's edits (delete any
    character, swap two neighbours, replace or insert a letter), or equal to e?
    Dictionary words are all a-z, so these checks match _edit1(e) & known exactly."""
    known = _known_words()
    plain, positional = _delete_index()
    if e in known or e in plain:                       # same word / insert a letter into e
        return True
    for i in range(len(e)):
        d = e[:i] + e[i + 1:]
        if d in known or f"{i}\x00{d}" in positional:  # delete e[i] / replace e[i]
            return True
        if i + 1 < len(e) and e[:i] + e[i + 1] + e[i] + e[i + 2:] in known:  # swap
            return True
    return False


@lru_cache(maxsize=200000)
def _has_correction(token):
    """For a lowercase token that is not a dictionary word: does Spelling.suggest()
    find any dictionary word within edit distance 2 (TextBlob's _edit1 applied twice)?

    The first edit is enumerated with TextBlob's own _edit1 (~500 strings); the second
    is answered with the deletion index instead of enumerating ~500 more per string.
    tests/test_spelling.py checks it against _has_correction_reference."""
    return any(_known_within_one_edit(e) for e in _spelling._edit1(token))


def is_misspelled(word):
    """Same answer as _misspelled_reference, but fast.

    Spelling.suggest() (textblob/_text.py) returns a token unchanged when it is one
    character, punctuation, whitespace, a number, or a dictionary word. Otherwise it
    returns the most probable dictionary word within edit distance 1, else 2, else the
    token itself. So an unknown *lowercase* token comes back changed exactly when some
    dictionary word is within edit distance 2; we test that existence directly.
    Title-case tokens (whose suggestions are re-capitalised) and anything else unusual
    go through the original correction. tests/test_spelling.py checks equality with
    the reference on real essays.
    """
    known = _known_words()
    for tok in regexp_tokenize(word, _BLOB_TOKEN):
        if (len(tok) == 1 or tok in _PUNCTUATION or tok.isspace()
                or tok.replace(".", "").isdigit() or tok in known):
            continue
        changed = _has_correction(tok) if tok.islower() and not tok.istitle() else _token_corrected(tok)
        if changed:
            return True
    return False

class FeatureExtractor(BaseEstimator, TransformerMixin):
    """Enhanced feature extraction for essay scoring"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
    def get_advanced_metrics(self, essay):
        """Extract advanced text metrics"""
        try:
            # Simple word splitting
            words = essay.lower().split()
            sentences = [s.strip() for s in essay.split('.') if s.strip()]
            
            return {
                'word_count': len(words),
                'sentence_count': len(sentences),
                'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
                'long_words': sum(1 for word in words if len(word) > 6),
                'unique_words': len(set(words)),
                'paragraph_count': len([p for p in essay.split('\n') if p.strip()])
            }
        except Exception as e:
            print(f"Error in advanced metrics: {str(e)}")
            return {
                'word_count': 0,
                'sentence_count': 0,
                'avg_word_length': 0,
                'long_words': 0,
                'unique_words': 0,
                'paragraph_count': 0
            }
    def get_readability_metrics(self, essay):
        """Calculate readability metrics"""
        try:
            # Simple sentence splitting using periods
            sentences = [s.strip() for s in essay.split('.') if s.strip()]
            # Simple word splitting
            words = essay.lower().split()
            
            if len(sentences) == 0 or len(words) == 0:
                return {
                    'avg_sent_length': 0,
                    'avg_word_length': 0,
                    'flesch_score': 0
                }
                
            avg_sent_length = len(words) / len(sentences)
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            return {
                'avg_sent_length': avg_sent_length,
                'avg_word_length': avg_word_length,
                'flesch_score': TextBlob(essay).sentiment.polarity
            }
        except Exception as e:
            print(f"Error in readability metrics: {str(e)}")
            return {
                'avg_sent_length': 0,
                'avg_word_length': 0,
                'flesch_score': 0
            }
    
    def get_grammar_metrics(self, essay):
        """Extract grammar and language usage features"""
        try:
            # Simple word splitting
            words = essay.lower().split()
            misspelled = 0
            
            # Use TextBlob for spell checking
            for word in words:
                if len(word) > 2 and is_misspelled(word):
                    misspelled += 1
            
            return {
                'grammar_errors': 0,
                'spelling_errors': misspelled,
                'style_errors': 0,
                'total_errors': misspelled
            }
        except Exception as e:
            print(f"Error in grammar metrics: {str(e)}")
            return {
                'grammar_errors': 0,
                'spelling_errors': 0,
                'style_errors': 0,
                'total_errors': 0
            }
    
    def get_coherence_metrics(self, essay):
        """Measure essay coherence and structure"""
        try:
            # Simple sentence and word splitting
            sentences = [s.strip() for s in essay.split('.') if s.strip()]
            words = essay.lower().split()
            
            # Get unique sentence starters
            sent_starters = []
            for sent in sentences:
                words_in_sent = sent.split()
                if words_in_sent:
                    sent_starters.append(words_in_sent[0].lower())
            
            return {
                'unique_sent_starts': len(set(sent_starters)),
                'vocab_richness': len(set(words)) / len(words) if words else 0
            }
        except Exception as e:
            print(f"Error in coherence metrics: {str(e)}")
            return {
                'unique_sent_starts': 0,
                'vocab_richness': 0
            }
    
    def get_argument_metrics(self, essay):
        """Analyze argument structure"""
        try:
            # Count discourse markers
            discourse_markers = ['however', 'therefore', 'furthermore', 'moreover',
                               'because', 'since', 'although', 'thus', 'hence']
            
            words = essay.lower().split()
            marker_count = sum(1 for word in words if word in discourse_markers)
            
            return {
                'discourse_markers': marker_count,
                'topic_development': len(words) / 100  # simplified metric
            }
        except Exception as e:
            print(f"Error in argument metrics: {str(e)}")
            return {
                'discourse_markers': 0,
                'topic_development': 0
            }
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        """Transform essays into features with progress bar"""
        features = []
        print("\nExtracting features from essays...")
        for essay in tqdm(X, desc="Processing essays"):
            try:
                essay_features = {}
                
                # Basic metrics
                readability = self.get_readability_metrics(essay)
                grammar = self.get_grammar_metrics(essay)
                coherence = self.get_coherence_metrics(essay)
                argument = self.get_argument_metrics(essay)
                advanced = self.get_advanced_metrics(essay)
                
                # Combine all metrics
                essay_features.update(readability)    # avg_sent_length, avg_word_length, flesch_score
                essay_features.update(grammar)        # grammar_errors, spelling_errors, style_errors, total_errors
                essay_features.update(coherence)      # unique_sent_starts, vocab_richness
                essay_features.update(argument)       # discourse_markers, topic_development
                essay_features.update(advanced)       # word_count, sentence_count, long_words, etc.
                
                # Calculate additional combined metrics
                total_words = advanced.get('word_count', 0)
                if total_words > 0:
                    essay_features['long_words_ratio'] = advanced.get('long_words', 0) / total_words
                    essay_features['unique_words_ratio'] = advanced.get('unique_words', 0) / total_words
                else:
                    essay_features['long_words_ratio'] = 0
                    essay_features['unique_words_ratio'] = 0
                
                # Add complexity metrics
                essay_features['complexity_score'] = (
                    essay_features['avg_word_length'] * 0.3 +
                    essay_features['long_words_ratio'] * 0.3 +
                    essay_features['unique_words_ratio'] * 0.2 +
                    essay_features['vocab_richness'] * 0.2
                )
                
                # Add coherence metrics
                essay_features['coherence_score'] = (
                    essay_features['unique_sent_starts'] * 0.4 +
                    essay_features['discourse_markers'] * 0.6
                )
                
                features.append(essay_features)
                
            except Exception as e:
                print(f"\nError processing essay: {str(e)}")
                # Add default values if processing fails
                features.append({
                    'avg_sent_length': 0,
                    'avg_word_length': 0,
                    'flesch_score': 0,
                    'grammar_errors': 0,
                    'spelling_errors': 0,
                    'style_errors': 0,
                    'total_errors': 0,
                    'unique_sent_starts': 0,
                    'vocab_richness': 0,
                    'discourse_markers': 0,
                    'topic_development': 0,
                    'word_count': 0,
                    'sentence_count': 0,
                    'avg_word_length': 0,
                    'long_words': 0,
                    'unique_words': 0,
                    'paragraph_count': 0,
                    'long_words_ratio': 0,
                    'unique_words_ratio': 0,
                    'complexity_score': 0,
                    'coherence_score': 0
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(features)
        
        # Fill any missing values with 0
        df = df.fillna(0)
        
        # Ensure all columns are numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    