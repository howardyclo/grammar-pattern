# grammar-pattern

This repo offers several python (3.x) modules for grammatical analysis:
1. Extracting grammar patterns from sentences. For example, the grammar pattern for **"discuss"** in the sentence **"He likes to discuss the issues ."** would be **"V n"**.
2. Aligning grammar patterns from parallel sentences. For example, grammatically erroneous source sentence **"He likes to discuss about the issues ."** → grammatically correct target sentence **"He likes to discuss the issues"**, the aligned grammar pattern for **"discuss"** would be **"V about n" → "V n"**.

We currently support grammar patterns for verb, noun and adjective headwords. See what grammar pattern is [in Wikipedia](https://en.wikipedia.org/wiki/Pattern_grammar).

## Setup
Before starting to use modules, please install the python dependencies (mainly [spaCy](https://spacy.io/) and [NLTK](https://www.nltk.org/)):
```sh
$ pip install -r requirements.txt

$ python -m spacy download en_core_web_lg 
```

You can simply run `test.py` to check if we miss some required modules or data.
```sh
$ python test.py
```

## Example Usages
Here we demonstrate how to test our shallow parser, extract grammar patterns for a sentence or align grammar patterns for parallel sentences.

### 0. Preprocess the sentences (See [How to use AllenNLP Constituency Tree Parser](how-to-use-allennlp-constituency-tree-parser/README.md))
Run an existing constituency tree parser to get linearized constituency tree string for every sentence as a pre-processing step. The constituency tree parser we use is [AllenNLP](https://github.com/allenai/allennlp). They have also an [online demo](http://demo.allennlp.org/constituency-parsing).
<br><br>
![Alt text](imgs/1.png)

### 1. Import modules
```python
from modules.shallow_parser import shallow_parse
from modules.grampat import sent_to_pats, align_parallel_pats
```

### 2. Get shallow parsed results from sentences
```python
# source sentence: "He liked to discuss about the issues ."
# target sentence: "He likes to discuss the issues ."
# Note that we parse sentences in advance using AllenNLP's constituency tree parser.

src_parsed = shallow_parse("(S (NP (PRP He)) (VP (VBD liked) (S (VP (TO to) (VP (VB discuss) (PP (IN about) (NP (DT the) (NNS issues))))))) (. .))")
tgt_parsed = shallow_parse("(S (NP (PRP He)) (VP (VBZ likes) (S (VP (TO to) (VP (VB discuss) (NP (DT the) (NNS issues)))))) (. .))")
```
```python 
print(src_parsed)

[[['He'], ['liked'], ['to'], ['discuss'], ['about'], ['the', 'issues'], ['.']],
 [['he'], ['like'], ['to'], ['discuss'], ['about'], ['the', 'issue'], ['.']],
 [['PRP'], ['VBD'], ['TO'], ['VB'], ['IN'], ['DT', 'NNS'], ['.']],
 [['H-NP'], ['H-VP'], ['H-VP'], ['H-VP'], ['H-PP'], ['I-NP', 'H-NP'], ['O']]]
```
```python
print(tgt_parsed)

[[['He'], ['likes'], ['to'], ['discuss'], ['the', 'issues'], ['.']],
 [['he'], ['like'], ['to'], ['discuss'], ['the', 'issue'], ['.']],
 [['PRP'], ['VBZ'], ['TO'], ['VB'], ['DT', 'NNS'], ['.']],
 [['H-NP'], ['H-VP'], ['H-VP'], ['H-VP'], ['I-NP', 'H-NP'], ['O']]]
```
`shallow_parse()` returns a list of chunked elements:
- Original words
- Base form of original words (lemmas)
- POS tag from constituency tree string
- Chunk tags

Note that the prefix `HIO` of chunk tags represents:
- `H`: Headword of a chunk. This is the headword of a grammar pattern we're interested in. We simply **select the last word of a chunk as our headword**.
- `I`: Non-headword of a chunk.
- `O`: Outside of a chunk. This is often a punctuation word and not important in our case.

### 3. Extract grammar patterns from sentences
```python
src_pats = sent_to_pats(src_parsed)
tgt_pats = sent_to_pats(tgt_parsed)
```
```python
print(src_pats)

[('LIKE', 'V to v', 'liked to discuss', (1, 3)),
 ('DISCUSS', 'V about n', 'discuss about the issues', (3, 5))]
```
```python
print(tgt_pats)

[('LIKE', 'V to v', 'likes to discuss', (1, 3)),
 ('DISCUSS', 'V n', 'discuss the issues', (3, 4))]
```
`sent_to_pats()` returns a list of tuples, each tuple contains:
- Headword
- Grammar pattern (POS tag in Uppercase corresponds to the headword.
- N-gram that matches grammar pattern
- Start and end positions of n-gram in chunked sentence.

How does `sent_to_pats()` works:
- Generate a list of n-grams of parsed results.
- For every n-gram, identify if **hand-selected** grammar patterns (listed in `grampat.py`) exist in an n-gram.
- The grammar patterns are selected from [*Collins COBUILD Grammar Patterns I: Verb*](http://arts-ccr-002.bham.ac.uk/ccr/patgram/) and [*Grammar Patterns II: Nouns and Adjectives*](https://www.amazon.com/Grammar-Patterns-II-Adjectives-COBUILD/dp/0003750671) in advance, which are annotated from experts. We believe those grammar patterns are generally good and able to cover most grammar patterns we used in English.
- Note that it is possible to automatically find good grammar patterns from large monolingual corpora by counting frequencies of various n-grams of POS tag, and select good n-grams of POS tag by frequency. We can roughly interpret grammar pattern as simplied n-gram of POS tag.

### 4. Align grammar patterns for parallel sentences
```python
parallel_pats = align_parallel_pats(src_pats, tgt_pats)
```
```python
print(parallel_pats)

[[('LIKE', 'V to v', 'liked to discuss', (1, 3)),
  ('LIKE', 'V to v', 'likes to discuss', (1, 3))],
 [('DISCUSS', 'V about n', 'discuss about the issues', (3, 5)),
  ('DISCUSS', 'V n', 'discuss the issues', (3, 4))]]
```
`align_parallel_pats()` returns a list of aligned grammar patterns.

## What's Next?
Now that you've completed the *Example Usages* guide, we can use these modules to count grammar patterns for large English monolingual corpora (BNC) and parallel grammatical error correction corpora (EFCAMDAT, LANG-8, CLC-FCE). We released a python script for doing this (support multi-processing):
<br><br>
```sh
$ python compute_grampat.py \
-in_src_path data/src.tree.txt \
-in_tgt_path data/tgt.tree.txt \
-out_path data \
-out_prefix dataset_name \
-n_jobs 4 \
-batch_size 1024
```

The data structure of the output file `data/dataset_name.grampat.dill` is a Python Dictionary containing two keys:

- `"count_dict"` (3-nested dict):
    - key1: source grammar pattern (str)
    - key2: target grammar pattern (str)
    - key3: headword in uppercase (str)
    - value: count
    - Note: We also save the instances that source grammar pattern is same as target grammar pattern.
- `"ngram_dict"` (4-nested dict):
    - key1: source grammar pattern (str)
    - key2: target grammar pattern (str)
    - key3: headword in uppercase (str)
    - key4: (source ngram, target ngram) (tuple)
    - value: count 

We released grammar pattern results for [BNC, EFCAMDAT, LANG-8 and CLC-FCE](https://goo.gl/aKR7Hr). It can be used for grammatical analysis (See `query_grampat.py` for example usage).