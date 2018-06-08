import re
import spacy
from spacy.tokens import Doc
from nltk.tree import ParentedTree
from collections import defaultdict

""" 
    -------------------------------------------------------------------------------------------------
    Customize spacy tokenizer to deal with tokenized sentence
    -------------------------------------------------------------------------------------------------
"""

class WhitespaceTokenizer(object):
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, text):
        words = text.split()
        # All tokens 'own' a subsequent space character in this tokenizer
        spaces = [True] * len(words)
        return Doc(self.vocab, words=words, spaces=spaces)
    
print('Loading SpaCy with custom whitespace tokenizer...')
nlp = spacy.load('en_core_web_lg', disable=['tagger', 'parser', 'textcat'])
nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)

""" 
    -------------------------------------------------------------------------------------------------
    Shallow parser from linearized constituency tree string
    We parse sentence with AllenNLP constituency tree parser first to get tree strings
    -------------------------------------------------------------------------------------------------
"""

def shallow_parse(tree_str):
    #------------------------------------------------------------------------------------------------
    # Inner functions
    #------------------------------------------------------------------------------------------------
    def _label_headword(chunk_tags):
        #  'H-'(head) prefix for the last word, otherwise 'I-'(non-head) as prefix.
        if 'O' in chunk_tags: return chunk_tags
        return ['I-' + chunk_tag if i != len(chunk_tags) - 1 else 'H-' + chunk_tag
                for i, chunk_tag in enumerate(chunk_tags)]
        
    def _positionize(lexicons):
        positions = []
        start, end = 0, 0
        for lexicon in lexicons:
            start = end
            end = start + len(lexicon)
            positions.append((start, end))
        return positions

    def _traverse_tree(tree, label_dict):
        for subtree in tree:
            # Leaf
            if subtree.height() < 3:
                leaf = subtree.leaves()[0]
                label = subtree.label()
                # Save traversed node's POS label
                label_dict[leaf]['POS'] = label

            # Non-leaf
            else:
                leaves_str = ' '.join(subtree.leaves())
                label = subtree.label()
                # Save traversed node's CHUNK label
                label_dict[leaves_str]['CHUNK'] = label

                _traverse_tree(subtree, label_dict)
    
    #------------------------------------------------------------------------------------------------
    # Main
    #------------------------------------------------------------------------------------------------
    
    # Get traversal history `label_dict`: {node_in_tree: {'POS': pos_tag, 'CHUNK': chunk_tag}}
    label_dict = defaultdict(lambda: defaultdict(lambda: str))
    tree = ParentedTree.fromstring(tree_str)
    _traverse_tree(tree, label_dict)
    
    # Get chunks from label_dict and get the minimum chunks.
    l = [k for k, v in label_dict.items() if 'CHUNK' in v.keys()]
    sorted_l = sorted(l, key=len, reverse=True)
    sorted_chunks = [j for i, j in enumerate(sorted_l) if not any(k in j for k in sorted_l[i + 1:])]
    chunks = [chunk for chunk in l if chunk in sorted_chunks] # re-sort
    
    # Assign chunk tag for every leaf.
    # The chunk tag is assigned from the leaf's minimum chunk.
    for leaf in tree.leaves():
        for chunk in sorted(l, key=len, reverse=False):
            if leaf in chunk.split():
                label_dict[leaf]['CHUNK'] = label_dict[chunk]['CHUNK']
                break
    
    # Annotate the chunks in the sentence for further tokenization and labeling.
    sent = ' '.join(tree.leaves())
    chunked_sent = sent
    for i, chunk in enumerate(chunks):
        chunked_sent = re.sub(re.escape(chunk), 'CHUNK:{}'.format('￭'.join(chunk.split())), chunked_sent)

    # Get chunked words and chunk tags.
    lexicons = [] # One word or a list of words (chunk)
    chunk_tags = []

    for lexicon in chunked_sent.split():
        # Detokenize labeled chunk
        if 'CHUNK:' in lexicon:
            lexicon = lexicon.replace('CHUNK:', '')
            lexicon = ' '.join(lexicon.split('￭'))
        
        # Label the lexcion
        chunk_tag = label_dict[lexicon].get('CHUNK', 'O')
        
        # Save results
        lexicons.append(lexicon.split())
        # Make chunk tag as same number as len(lexicon) and tag 'H'/'I' prefix for each chunk tag.
        chunk_tags.append(_label_headword([chunk_tag]*len(lexicons[-1])))

    # Get chunk positions (start, end) in order to chunk other sequence.
    positions = _positionize(lexicons)

    # Get chunked lemmas.
    lemmas = [tok.lemma_.lower() if tok.lemma_ != '-PRON-' else tok.text.lower() for tok in nlp(sent)]
    lemmas = [lemmas[start:end] for start, end in positions]

    # Get chunked pos tags.
    pos_tags = [label_dict[tok].get('POS') for tok in sent.split()]
    pos_tags = [pos_tags[start:end] for start, end in positions]
    
    return [lexicons, lemmas, pos_tags, chunk_tags]