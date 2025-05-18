import heapq

from guess.pcfg_guesser import PCFGGuesser


class QueueItem:
    def __init__(self, node):
        self.node = node

    def __lt__(self, other):
        return self.node.prob > other.node.prob

    def __le__(self, other):
        return self.node.prob >= other.node.prob

    def __eq__(self, other):
        return self.node.prob == other.node.prob

    def __ne__(self, other):
        return self.node.prob != other.node.prob

    def __gt__(self, other):
        return self.node.prob < other.node.prob

    def __ge__(self, other):
        return self.node.prob <= other.node.prob

class PcfgQueue:
    def __init__(self, pcfg : PCFGGuesser):
        self.pcfg = pcfg
        self.queue = []
        self.max_probability = 1.0
        self.min_probability = 0.0
        self.max_queue_size = 50000

        for base_item in self.pcfg.initialize_base_structures():
            heapq.heappush(self.queue, QueueItem(base_item))

    def next(self):
        if not self.queue:
            return None

        queue_item = heapq.heappop(self.queue)
        self.max_probability = queue_item.node.prob

        for child in self.pcfg.find_children(queue_item.node):
            heapq.heappush(self.queue, QueueItem(child))

        return queue_item.node
