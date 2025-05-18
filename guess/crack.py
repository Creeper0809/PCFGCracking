import math

from guess.pcfg_guesser import PCFGGuesser, TreeItem
from guess.priority_queue import PcfgQueue

def debug(structures):
    structurestr = ""
    for structure in structures:
        structurestr += structure.symbol
    return structurestr

def start_guess():
    pcfg = PCFGGuesser()
    queue = PcfgQueue(pcfg=pcfg)
    password_count = 0
    while True:
        next_node : TreeItem = queue.next()
        if next_node is None:
            break
        print(f"current structure : {debug(next_node.structures)}")
        print(f"made password count : {password_count }")
        print(f"prob : {math.exp(next_node.prob) * 100}%")
        print("password : ",end="")
        password_count += pcfg.guess(next_node.structures)
        print("-"*40)

if __name__ == '__main__':
    start_guess()