""" 
    -------------------------------------------------------------------------------------------------
    Extract grammar patterns from shallow parsed results
    1. Generate N-grams for tokenized/chunked sentence
    2. Identify grammar pattern for every N-grams
    -------------------------------------------------------------------------------------------------
"""

pgPreps = 'in_favor_of|_|about|after|against|among|as|at|between|behind|by|for|from|in|into|of|on|upon|over|through|to|towards|toward|under|with'.split('|')
otherPreps ='out|'.split('|')
verbpat = ('V; V n; V ord; V oneself; V adj; V v-ing; V to v; V v; V that; V wh; V wh to v; V quote; '+\
           'V so; V not; V as if; V as though; V someway; V together; V as adj; V as to wh; V by amount; '+\
           'V amount; V by v-ing; V in favour of n; V in favour of v-ing; V n in favour of n; V n in favour of v-ing; V n n; V n adj; V n v-ing; V n to v; V n v n; V n that; '+\
           'V n wh; V n wh to v; V n with quote; V n v-ed; ' +\
           'V n someway; V n with together; '+\
           'V n as adj; V n into v-ing; V adv; V and v').split('; ')
verbpat += ['V %s n' % prep for prep in pgPreps]+['V n %s n' % prep for prep in verbpat]
verbpat += [pat.replace('V ', 'V-ed ') for pat in verbpat]
pgNoun = ('N for n to v; N from n that; N from n to v; N from n for n; N in favor of; N in favour of; '+\
            'N of amount; N of n as n; N of n to n; N of n with n; N on n for n; N on n to v'+\
            'N that; N to v; N to n that; N to n to v; N with n for n; N with n that; N with n to v').split('; ')
pgNoun += pgNoun + ['N %s v-ing' % prep for prep in pgPreps ]
pgNoun += pgNoun + ['ADJ %s n' % prep for prep in pgPreps if prep != 'of']+ ['N %s v-ing' % prep for prep in pgPreps]
pgAdj = ('ADJ adj; ADJ and adj; ADJ as to wh; '+\
        'ADJ enough; ADJ enough for n; ADJ enough for n to v; ADJ enough n; '+\
        'ADJ enough n for n; ADJ enough n for n to v; ADJ enough n that; ADJ enough to v; '+\
        'ADJ for n to v; ADJ from n to n; ADJ in color; ADJ v-ing; '+\
        'ADJ in n as n; ADJ in n from n; ADJ in n to n; ADJ in n with n; ADJ in n as n; ADJ n for n'+\
        'ADJ n to v; ADJ on n for n; ADJ on n to v; ADJ that; ADJ to v; ADJ to n for n; ADJ n for v-ing'+\
        'ADJ wh; ADJ on n for n; ADJ on n to v; ADJ that; ADJ to v; ADJ to n for n; ADJ n for v-ing').split('; ')
pgAdj += ['ADJ %s n'%prep for prep in pgPreps]
reservedWords = 'how wh; who wh; what wh; when wh; someway someway; together together; that that'.split('; ')
pronOBJ = ['me', 'us', 'you', 'him', 'them']
mapHead = dict( [('H-NP', 'N'), ('H-VP', 'V'), ('H-VB', 'V'), ('H-ADJP', 'ADJ'), ('H-ADVP', 'ADV')] )
mapRest = dict( [('VBG', 'v-ing'), ('VBD', 'v-ed'), ('VBN', 'v-ed'), ('VB', 'v'), ('NN', 'n'), ('NNS', 'n'),
                 ('JJ', 'adj'), ('RB', 'adv')] )
mapRW = dict( [ pair.split() for pair in reservedWords ] )

def sent_to_ngram(words, lemmas, tags, chunks):
    """ Returns a list of tuple(start, end) """
    maxDegree = 9
    return [(k, k+degree) for k in range(0, len(words)) for degree in range(2, min(maxDegree, len(words)-k+1))]

def ngram_to_head(words, lemmas, tags, chunks, start, end):
    """ Headword would usually be the last word of chunk.
        Find the tag of the headword which POS tag is
        verb, noun or adjective with/without following an adverb(RP).
    """
    for i in range(start, end): 
        if tags[i][-1][0] in ['V', 'N', 'J'] and tags[i+1][-1] == 'RP':
            return lemmas[i][-1].upper() + ('_'+lemmas[i+1][-1].upper())
        if tags[i][-1][0] in ['V', 'N', 'J']:
            return lemmas[i][-1].upper()
        
def ngram_to_pats(words, lemmas, tags, chunks, start, end):
    #------------------------------------------------------------------------------------------------
    # Inner functions
    #------------------------------------------------------------------------------------------------
    def _chunk_to_element(words, lemmas, tags, chunks, i, isHead):
        def _has_two_objs(tag, chunk):
            if chunk[-1] != 'H-NP': return False
            return (len(tag) > 1 and tag[0] in pronOBJ) or (len(tag) > 1 and 'DT' in tag[1:])    
        
        if isHead and not tags[i][-1] == 'TO': return mapHead[chunks[i][-1]] if chunks[i][-1] in mapHead else '*'
        if tags[i][-1] == 'TO': return 'to' # Make "V to(H-VP) v" to ""V to v" instead "V v v". 
        if lemmas[i][0] == 'favour' and words[i-1][-1] == 'in' and words[i+1][0] == 'of':
                                                              return 'favour'
        
        if tags[i][-1] == 'RP' and tags[i-1][-1][:2] == 'VB': return '_'
        if tags[i][0][0] == 'W' and lemmas[i][-1] in mapRW:     return mapRW[lemmas[i][-1]]
        if _has_two_objs(tags[i], chunks[i]):                 return 'n n'
        if tags[i][-1] == 'CD':                                 return 'amount'
        if tags[i][-1] == 'RB' and lemmas[i][-1] in ['enough', 'someway', 'together']:
                                                              return lemmas[i][-1]
        if tags[i][-1] in mapRest:                            return mapRest[tags[i][-1]]
        if tags[i][-1][:2] in mapRest:                        return mapRest[tags[i][-1][:2]]
        if chunks[i][-1] in mapHead:                          return mapHead[chunks[i][-1]].lower()
        if lemmas[i][-1] in pgPreps:                          return lemmas[i][-1]
        return lemmas[i][-1]

    def _simplify_pat(pat):
        return 'V' if pat == 'V ,' else pat.replace(' _', '').replace('_', ' ').replace('  ', ' ')

    def _is_cobuild_pattern(pat):
        global verbpat, pgNoun, pgAdj
        return pat in verbpat + pgNoun + pgAdj
    
    #------------------------------------------------------------------------------------------------
    # Main
    #------------------------------------------------------------------------------------------------
    pat, doneHead = [], False
    
    for i in range(start, end):
        isHead = tags[i][-1][0] in ['V', 'N', 'J'] and not doneHead
        pat.append(_chunk_to_element(words, lemmas, tags, chunks, i, isHead))
        if isHead: doneHead = True
    pat = _simplify_pat(' '.join(pat))
    
    return pat if _is_cobuild_pattern(pat) else ''

def sent_to_pats(parsed):
    """ Main API for extracting grammar patterns from parsed results.
    `parsed`: Parsed results from shallow parser
    """
    pats = []
    for start, end in sent_to_ngram(*parsed):
        pat = ngram_to_pats(*parsed, start, end)
        if pat: 
            head = ngram_to_head(*parsed, start, end)
            lexicons = ' '.join([' '.join(x) for x in parsed[0][start:end] ])
            pats.append((head, pat, lexicons, (start, end-1)))
    return pats

def align_parallel_pats(src_pats, tgt_pats):
    """ Main API for aligning grammar patterns from parallel sentences
    `src_pats`: Results from `sent_to_pats` of a source sentence.
    `tgt_pats`: Results from `sent_to_pats` of a target sentence.
    """
    # Intersecting the common headwords.
    src_heads = set([pat[0] for pat in src_pats])
    tgt_heads = set([pat[0] for pat in tgt_pats])
    intersect_heads = list(src_heads & tgt_heads)

    # Group parallel patterns by common headword.
    # `grouped_parallel_pats` = [[ src_pats, tgt_pats ], ...]
    # Each [ src_pats, tgt_pats ] is grouped by headword.
    # Since len(src_pats) probabily !== len(tgt_pats), we need to assure they are 1-to-1 mapping.
    grouped_parallel_pats = []
    for head in intersect_heads:
        grouped_parallel_pats.append([list(filter(lambda pat: pat[0] in head, src_pats)),
                                      list(filter(lambda pat: pat[0] in head, tgt_pats))])

    # Align parallel patterns from grouped parallel patterns
    # `parallel_pats` = [[src_pat, tgt_pat], ...]
    parallel_pats = []
    for grouped_parallel_pat in grouped_parallel_pats: 
        src_pats_, tgt_pats_ = grouped_parallel_pat[0], grouped_parallel_pat[1]
        # Map parallel patterns one by one (they are ordered already.)
        while len(src_pats_) and len(tgt_pats_):
            parallel_pats.append([src_pats_.pop(0), tgt_pats_.pop(0)])
        
    return parallel_pats