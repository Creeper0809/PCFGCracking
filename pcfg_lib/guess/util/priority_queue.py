import heapq
from pcfg_lib.guess.pcfg.pcfg_guesser import PCFGGuesser, TreeItem


class QueueItem:
    def __init__(self, node: TreeItem):
        self.node = node
    def __lt__(self, other):   return self.node.prob > other.node.prob
    def __le__(self, other):   return self.node.prob >= other.node.prob
    def __eq__(self, other):   return self.node.prob == other.node.prob
    def __ne__(self, other):   return self.node.prob != other.node.prob
    def __gt__(self, other):   return self.node.prob < other.node.prob
    def __ge__(self, other):   return self.node.prob <= other.node.prob


class PcfgQueue:
    def __init__(self, pcfg: PCFGGuesser):
        self.pcfg = pcfg
        self._heap: list[QueueItem] = []
        for base in self.pcfg.initialize_base_structures():
            heapq.heappush(self._heap, QueueItem(base))

    def pop(self) -> TreeItem | None:
        if not self._heap:
            return None
        qi = heapq.heappop(self._heap)
        return qi.node

    def push(self, node: TreeItem):
        heapq.heappush(self._heap, QueueItem(node))
