from modules.shallow_parser import shallow_parse
from modules.grampat import sent_to_pats, align_parallel_pats

src_parsed = shallow_parse("(S (NP (PRP He)) (VP (VBD liked) (S (VP (TO to) (VP (VB discuss) (PP (IN about) (NP (DT the) (NNS issues))))))) (. .))")
tgt_parsed = shallow_parse("(S (NP (PRP He)) (VP (VBZ likes) (S (VP (TO to) (VP (VB discuss) (NP (DT the) (NNS issues)))))) (. .))")

src_pats = sent_to_pats(src_parsed)
tgt_pats = sent_to_pats(tgt_parsed)

parallel_pats = align_parallel_pats(src_pats, tgt_pats)

print('Test done. We are good to go!')