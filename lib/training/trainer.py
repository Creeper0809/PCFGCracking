import sys
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from itertools import islice
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from lib import config
from lib.training.pcfg.pcfg_parser import PCFGParser
from lib.training.pcfg.pcfg_output import save_pcfg_to_sqlite
from lib.training.pcfg.word_trie import WordTrie
from lib.training.omen.omen_parser import AlphabetGrammar, find_omen_level
from lib.training.omen.evaluate_password import calc_omen_keyspace
from lib.training.omen.omen_train_data_output import save_omen_to_sqlite
from lib.training.io.train_data_parser import TrainingDataParser

def chunked_iterator(iterator, size):
    it = iter(iterator)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk

def _worker_chunk(chunk, info):
    trie = WordTrie(needed_appear=info['needed_appear'])
    p = PCFGParser(trie)
    o = AlphabetGrammar(
        ngram=info['ngram'],
        min_length=info['min_length'],
        max_length=info['max_length']
    )
    for pwd in chunk:
        p.parse(pwd)
        o.parse(pwd)
    p.caculate_word_tree()
    return (
        {
            'keyboard': p.count_keyboard,
            'years': p.count_years,
            'alpha': p.count_alpha,
            'alpha_masks': p.count_alpha_masks,
            'digits': p.count_digits,
            'special': p.count_special,
            'korean': p.count_korean,
            'base_structures': p.count_base_structures,
            'prince': p.count_prince
        },
        o.grammar,
        o.count_at_start,
        o.count_at_end
    )

def merge_counters(list_of_dicts):
    merged = {}
    for d in list_of_dicts:
        for key, counter in d.items():
            if key not in merged:
                if isinstance(counter, Counter):
                    merged[key] = Counter()
                else:
                    merged[key] = defaultdict(Counter)
            if isinstance(counter, Counter):
                merged[key].update(counter)
            else:
                for inner_key, inner_counter in counter.items():
                    merged[key][inner_key].update(inner_counter)
    return merged

def merge_grammar(dicts):
    merged = {}
    for grammar in dicts:
        for k, node in grammar.items():
            if k not in merged:
                merged[k] = type(node)()
            m = merged[k]
            m.count_at_start += node.count_at_start
            m.count_in_middle += node.count_in_middle
            m.count_at_end += node.count_at_end
            for nxt, c in node.next_letter_candidates.items():
                m.next_letter_candidates[nxt] = m.next_letter_candidates.get(nxt, 0) + c
    return merged

def start_train(program_info: dict, chunk_size: int = 10000):
    parser = TrainingDataParser(
        min_length=program_info['min_length'],
        max_length=program_info['max_length'],
        filedir=program_info['data'],
        encoding=program_info.get('encoding', 'utf-8')
    )
    total = parser.count_passwords()
    workers = 8
    pcfg_results = []
    omen_grammars = []
    start_counts = []
    end_counts = []

    with ProcessPoolExecutor(max_workers=workers) as executor, Progress(
        "[bold green]Training...[/]",
        BarColumn(),
        "{task.completed}/{task.total}",
        TimeElapsedColumn(),
        TimeRemainingColumn()
    ) as progress:
        task = progress.add_task("Parsing", total=total)
        futures = {}
        for chunk in chunked_iterator(parser.read_password(), chunk_size):
            f = executor.submit(_worker_chunk, chunk, program_info)
            futures[f] = len(chunk)
        for f in as_completed(futures):
            try:
                pcfg_counts, omen_gram, cstart, cend = f.result()
            except Exception:
                traceback.print_exc()
                sys.exit(1)
            pcfg_results.append(pcfg_counts)
            omen_grammars.append(omen_gram)
            start_counts.append(cstart)
            end_counts.append(cend)
            progress.advance(task, futures[f])

    merged_pcfg = merge_counters(pcfg_results)
    merged_omen_grammar = merge_grammar(omen_grammars)
    total_start = sum(start_counts)
    total_end = sum(end_counts)

    pcfg = PCFGParser(WordTrie(needed_appear=program_info['needed_appear']))
    pcfg.count_keyboard = merged_pcfg['keyboard']
    pcfg.count_years = merged_pcfg['years']
    pcfg.count_alpha = merged_pcfg['alpha']
    pcfg.count_alpha_masks = merged_pcfg['alpha_masks']
    pcfg.count_digits = merged_pcfg['digits']
    pcfg.count_special = merged_pcfg['special']
    pcfg.count_korean = merged_pcfg['korean']
    pcfg.count_base_structures = merged_pcfg['base_structures']
    pcfg.count_prince = merged_pcfg['prince']

    omen = AlphabetGrammar(
        ngram=program_info['ngram'],
        min_length=program_info['min_length'],
        max_length=program_info['max_length']
    )
    omen.grammar = merged_omen_grammar
    omen.count_at_start = total_start
    omen.count_at_end = total_end
    omen.apply_smoothing()
    keyspace = calc_omen_keyspace(omen)

    levels = Counter()
    parser.num_passwords = 0
    with Progress(
        "[bold blue]Level count...[/]",
        BarColumn(),
        "{task.completed}/{task.total}",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        transient=True
    ) as progress2:
        task2 = progress2.add_task("Counting", total=total)
        for pwd in parser.read_password():
            levels[find_omen_level(omen, pwd)] += 1
            progress2.advance(task2)

    dbfile = str(config.ROOT_PATH / 'sqlite3.db')
    save_pcfg_to_sqlite(pcfg_parser=pcfg, db_path=dbfile)
    save_omen_to_sqlite(
        alphabet_grammar=omen,
        omen_keyspace=keyspace,
        omen_levels_count=levels,
        num_valid_passwords=parser.num_passwords,
        db_path=dbfile,
        program_info=program_info
    )
    parser.close()
    print("[DONE] Parallel training complete")
