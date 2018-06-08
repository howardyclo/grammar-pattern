import os
import dill 
import argparse
from collections import defaultdict
from joblib import Parallel, delayed
from modules.shallow_parser import shallow_parse
from modules.grampat import sent_to_pats, align_parallel_pats

def lazily_read_parallel(src_file, tgt_file, batch_size=1024):
    """ Lazy version of for ... in zip(src_file, tgt_file) """
    stop = False
    while not stop:
        parallel_lines = []
        for _ in range(batch_size):
            src_line = src_file.readline().strip()
            tgt_line = tgt_file.readline().strip()
            if not src_line or not tgt_line:
                continue
            if src_line and tgt_line:
                parallel_lines.append((src_line, tgt_line))
            else: 
                stop = True
                break
        yield parallel_lines
        
def func_to_parallel(parallel_line):
    src_tree_str, tgt_tree_str = parallel_line
    parallel_pats = []
    try:
        src_pats = sent_to_pats(shallow_parse(eval(src_tree_str)))
        tgt_pats = sent_to_pats(shallow_parse(eval(tgt_tree_str)))
        parallel_pats = align_parallel_pats(src_pats, tgt_pats)
    except:
        pass
    return parallel_pats
        
def main(args):
    """
        Compute statistics:
        
        - `count_dict` (3-nested dict):
            - key1: source grammar pattern (str)
            - key2: target grammar pattern (str)
            - key3: headword in uppercase (str)
            - value: count
            - Note: We also save the instances that source grammar pattern is same as target grammar pattern.
        - `ngram_dict` (3-nested dict):
            - key1: source grammar pattern (str)
            - key2: target grammar pattern (str)
            - key3: headword in uppercase (str)
            - value: list of tuple (source ngram, target ngram) (list)
            - Note: value may contain several identical tuples, you can filter by `set()`.
    """
        
    # parallel_pat_dict[src_pat][tgt_pat][head]: count
    # note that src_pat may be as same as tgt_pat
    count_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # ngram examples for parallel grammar patterns
    # parallel_ngram[src_pat][tgt_pat][head]: (src_ngram, tgt_ngram)
    ngram_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    
    # Check output path is exists, otherwise create one.
    if not os.path.exists(args.out_path):
        os.makedirs(args.out_path)
    
    # Print output paths for sanity-check.
    out_path = os.path.join(args.out_path, '{}.grampat.dill'.format(args.out_prefix))
    print('Statistics will be saved to "{}"...'.format(out_path))
    
    with open(args.in_src_path) as in_src_file, open(args.in_tgt_path) as in_tgt_file,\
        open(out_path, 'wb') as out_file,\
        Parallel(n_jobs=args.n_jobs) as parallel:

        # Check if parallel files have the same line count.
        in_src_file_len = len(in_src_file.readlines())
        in_tgt_file_len = len(in_tgt_file.readlines())
        assert in_src_file_len == in_tgt_file_len
        in_src_file.seek(0), in_tgt_file.seek(0)
        
        # Get total line count.
        num_iteration = in_src_file_len // args.batch_size + 1
        
        # Start processing.
        for batch_id, parallel_lines in enumerate(lazily_read_parallel(in_src_file, in_tgt_file, batch_size=args.batch_size)):
            print('Processing batch: {}/{}...'.format(batch_id+1, num_iteration), end='\r')
            parallel_pats = parallel(delayed(func_to_parallel)(parallel_line) for parallel_line in parallel_lines)
            # Save statistics
            # `parallel_pats`: parallel grammmar patterns of every parallel sentences
            for pats in parallel_pats:
                for parallel_pat in pats:
                    head, src_pat, src_ngram, _ = parallel_pat[0]
                    head, tgt_pat, tgt_ngram, _ = parallel_pat[1]
                    count_dict[src_pat][tgt_pat][head] += 1
                    ngram_dict[src_pat][tgt_pat][head][(src_ngram, tgt_ngram)] += 1
            
            print('Done batch: {}/{}...'.format(batch_id+1, num_iteration), end='\r')
            
            # Stop
            if batch_id + 1 == num_iteration:
                break
        
        # Save statistics to file
        print('Saving statistics to "{}"...'.format(out_path))
        
        dill.dump({
            'count_dict': count_dict,
            'ngram_dict': ngram_dict
        }, out_file)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get statistics of parallel grammar patterns and examples')
    parser.add_argument('-in_src_path', type=str, required=True,
                        help='The source *file* path to the input file contained sentences seperated by newline.')
    parser.add_argument('-in_tgt_path', type=str, required=True,
                        help='The target *file* path to the input file contained sentences seperated by newline.')
    parser.add_argument('-out_path', type=str, required=True,
                        help='The *folder* path to the output files.')
    parser.add_argument('-out_prefix', type=str, required=True,
                        help='The prefix file name for statistic files.')
    parser.add_argument('-n_jobs', type=int, default=8,
                        help='The maximum number of concurrently running jobs for detokenization.')
    parser.add_argument('-batch_size', type=int, default=4096,
                        help='The number of sentences to lazily processed by spacy pipeline.')
    args = parser.parse_args()
    main(args)