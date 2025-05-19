import math
import time

from guess.pcfg_guesser import PCFGGuesser, TreeItem
from guess.priority_queue import PcfgQueue

def start_guess():
    pcfg = PCFGGuesser()
    queue = PcfgQueue(pcfg=pcfg)
    password_count = 0

    print("")
    print("")
    print("")
    print("start guessing...")
    print("-"*40)
    start = time.time()

    while True:
        next_node : TreeItem = queue.next()
        if next_node is None:
            break
        print(f"current structure : {"".join(structure.symbol for structure in next_node.structures)}")
        print(f"prob : {math.exp(next_node.prob) * 100}%")
        print("passwords : ")
        count = pcfg.guess(next_node.structures)
        password_count += count
        print(f"made password count : {count}")
        print(f"total password count : {password_count}")
        print("-"*40)

    end = time.time()
    print("end guessing...")
    print(f"time taken : {end-start} sec")

if __name__ == '__main__':
    start_guess()