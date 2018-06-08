import dill
import operator
from collections import defaultdict

def load_files():
        
    with open('bnc.grampat.dill', 'rb') as f:
        bnc = dill.load(f)
        
    with open('clcfce.grampat.dill', 'rb') as f:
        clcfce = dill.load(f)
        
    with open('efcamdat.grampat.dill', 'rb') as f:
        efcamdat = dill.load(f)
        
    with open('lang8.grampat.dill', 'rb') as f:
        lang8 = dill.load(f)
        
    return bnc, clcfce, efcamdat, lang8

def get_head_stpat_dict(count_dict):
    """
        Inverse the `count_dict` [src_pat][tgt_pat][headword] to [head][src_pat][tgt_pat].
    """
    
    head_stpat_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for src_pat, tgt_dict in count_dict.items():
        for tgt_pat, head_dict in tgt_dict.items():
            for head, count in head_dict.items():
                if count:
                    # src -> tgt
                    head_stpat_dict[head][src_pat][tgt_pat] = count
                    head_stpat_dict['*'][src_pat][tgt_pat] += count
                    head_stpat_dict[head]['*'][tgt_pat] += count
                    head_stpat_dict[head][src_pat]['*'] += count
    return head_stpat_dict

def get_inconsistent_dict(head_stpat_dict):
    """ 
        Find inconsistent grammar patterns for each headword, for example,
        there exists either `src_pat` -> `tgt_pat` or `tgt_pat` -> `src_pat` for the specific headword.
    """
    
    # These preps are copied from Jason's `grampat.py`
    pgPreps = 'in_favor_of|_|about|after|against|among|as|at|between|behind|by|for|from|in|into|of|\
    on|upon|over|through|to|towards|toward|under|with'.split('|')
    otherPreps ='out|'.split('|')
    Preps = set(pgPreps + otherPreps)
    
    inconsistent_dict = defaultdict(list)

    for head in head_stpat_dict.keys():
        if head == '*': continue
        visited_pats = []
        for src_pat in head_stpat_dict[head].keys():
            for tgt_pat in head_stpat_dict[head][src_pat].keys():
                # Find parallel grammars exists in either src->tgt or tgt->src (inconsistency)
                # And only keep parallel changes involved preposition words
                if src_pat != '*' and tgt_pat != '*' and src_pat != tgt_pat \
                and head_stpat_dict[head].get(tgt_pat) and head_stpat_dict[head][tgt_pat].get(src_pat)\
                and {src_pat, tgt_pat} not in visited_pats\
                and set(src_pat.split()).symmetric_difference(set(tgt_pat.split()))\
                and not set(src_pat.split()).symmetric_difference(set(tgt_pat.split())) - Preps:
                    inconsistent_dict[head].append({
                        f'{src_pat} -> {tgt_pat}': head_stpat_dict[head][src_pat][tgt_pat],
                        f'{tgt_pat} -> {src_pat}': head_stpat_dict[head][tgt_pat][src_pat],
                        f'{src_pat} -> {src_pat}': head_stpat_dict[head][src_pat].get(src_pat, 0),
                        f'{tgt_pat} -> {tgt_pat}': head_stpat_dict[head][tgt_pat].get(tgt_pat, 0)
                    })
                    visited_pats.append({src_pat, tgt_pat})
    return inconsistent_dict

if __name__ == '__main__':
    """
        Data structure of dill object:
        - `count_dict` (3-nested dict):
            - key1: source grammar pattern (str), e.g., "V about n"
            - key2: target grammar pattern (str), e.g., "V n
            - key3: headword in uppercase (str), e.g., "DISCUSS"
            - value: count
        - `ngram_dict` (3-nested dict):
            - key1: source grammar pattern (str), e.g., "V about n"
            - key2: target grammar pattern (str), e.g., "V n
            - key3: headword in uppercase (str), e.g., "DISCUSS"
            - key4: tuple (source ngram, target ngram),
                    e.g., ("discuss about something", "discuss something")
            - value: count

        Notes:
        - Current dictionaries are queried by parallel grammar patterns.
          If you want to query by `headword`, use `get_head_stpat_dict()`.
        - BNC grampat's source & target grammar pattern will be the same.        
    """
    
    #---------------------------------------------------------------------------
    # 1. Load files
    #---------------------------------------------------------------------------
    bnc, clcfce, efcamdat, lang8 = load_files()
    
    #---------------------------------------------------------------------------
    # 2. Show top 5 headwords of 'V about n' -> 'V n'
    # Here we show headwords in EFCAMDAT, you can query another corpora as well.
    #---------------------------------------------------------------------------
    topk = 5
    src_pat = 'V about n'
    tgt_pat = 'V n'
    
    print('Top {} headwords that exists "{} -> {}" in EFCAMDAT:'.format(topk, src_pat, tgt_pat))
    print(sorted(efcamdat['count_dict'][src_pat][tgt_pat].items(), key=operator.itemgetter(1), reverse=True)[:topk])
    print()
    
    #---------------------------------------------------------------------------
    # 3. Show top 5 ngram examples of 'DISCUSS about n' -> 'DISCUSS n'
    # Here we show headwords in EFCAMDAT, you can query another corpora as well.
    #---------------------------------------------------------------------------
    topk = 5
    src_pat = 'V about n'
    tgt_pat = 'V n'
    head = 'DISCUSS'
    
    print('Top {} n-gram examples of "{} -> {}" of the headword "{}" in EFCAMDAT:'.format(topk, src_pat, tgt_pat, head))
    for ((src_ngram, tgt_ngram), count) in sorted(efcamdat['ngram_dict'][src_pat][tgt_pat][head].items(),\
                                                  key=operator.itemgetter(1), reverse=True)[:5]:
        print('{} -> {}: {}'.format(src_ngram, tgt_ngram, count))
    print()
    
    #---------------------------------------------------------------------------
    # 4. Show counts of parallel grammar pattern of the specific headword.
    # Note that since BNC is a monolingual corpus, thus `src_pat` == `tgt_pat`.
    #---------------------------------------------------------------------------
    src_pat = 'V about n'
    tgt_pat = 'V n'
    head = 'DISCUSS'
    
    print('Grammar pattern counts of "{}" in BNC:'.format(head))
    print('{} -> {}: {}'.format(src_pat, src_pat, bnc['count_dict'][src_pat][src_pat][head]))
    print('{} -> {}: {}'.format(src_pat, tgt_pat, bnc['count_dict'][src_pat][tgt_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, src_pat, bnc['count_dict'][tgt_pat][src_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, tgt_pat, bnc['count_dict'][tgt_pat][tgt_pat][head]))
    print()
    
    print('Grammar pattern counts of "{}" in CLC-FCE:'.format(head))
    print('{} -> {}: {}'.format(src_pat, src_pat, clcfce['count_dict'][src_pat][src_pat][head]))
    print('{} -> {}: {}'.format(src_pat, tgt_pat, clcfce['count_dict'][src_pat][tgt_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, src_pat, clcfce['count_dict'][tgt_pat][src_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, tgt_pat, clcfce['count_dict'][tgt_pat][tgt_pat][head]))
    print()
    
    print('Grammar pattern counts of "{}" in EFCAMDAT:'.format(head))
    print('{} -> {}: {}'.format(src_pat, src_pat, efcamdat['count_dict'][src_pat][src_pat][head]))
    print('{} -> {}: {}'.format(src_pat, tgt_pat, efcamdat['count_dict'][src_pat][tgt_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, src_pat, efcamdat['count_dict'][tgt_pat][src_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, tgt_pat, efcamdat['count_dict'][tgt_pat][tgt_pat][head]))
    print()
    
    print('Grammar pattern counts of "{}" in LANG8:'.format(head))
    print('{} -> {}: {}'.format(src_pat, src_pat, lang8['count_dict'][src_pat][src_pat][head]))
    print('{} -> {}: {}'.format(src_pat, tgt_pat, lang8['count_dict'][src_pat][tgt_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, src_pat, lang8['count_dict'][tgt_pat][src_pat][head]))
    print('{} -> {}: {}'.format(tgt_pat, tgt_pat, lang8['count_dict'][tgt_pat][tgt_pat][head]))
    print()

    #---------------------------------------------------------------------------
    # 5. Find inconsistent parallel grammar patterns for every headword
    #    that only involve changes of preposition.
    #---------------------------------------------------------------------------
    efcamdat['head_stpat_dict'] = get_head_stpat_dict(efcamdat['count_dict'])
    efcamdat['inconsistent_dict'] = get_inconsistent_dict(efcamdat['head_stpat_dict'])
    clcfce['head_stpat_dict'] = get_head_stpat_dict(clcfce['count_dict'])
    clcfce['inconsistent_dict'] = get_inconsistent_dict(clcfce['head_stpat_dict'])
    lang8['head_stpat_dict'] = get_head_stpat_dict(lang8['count_dict'])
    lang8['inconsistent_dict'] = get_inconsistent_dict(lang8['head_stpat_dict'])
    
    #---------------------------------------------------------------------------
    # 6. Show inconsistent parallel grammar patterns of the headword "DISCUSS"
    #    in EFCAMDAT.
    #---------------------------------------------------------------------------
    head = 'DISCUSS'
    
    print('Inconsistent parallel grammar patterns of the headword "{}" in EFCAMDAT:'.format(head))
    for i, inconsistent_case in enumerate(efcamdat['inconsistent_dict'][head]):
        print('Case {}:'.format(i+1))
        for parallel_grampat, count in inconsistent_case.items():
            print('{}: {}'.format(parallel_grampat, count))
        print()
    print()