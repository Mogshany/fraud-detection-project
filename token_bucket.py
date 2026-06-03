import time, threading
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity=capacity; self.tokens=capacity
        self.refill_rate=refill_rate; self.last=time.time()
        self.lock=threading.Lock()
    def refill(self):
        now=time.time(); dt=now-self.last
        self.tokens=min(self.capacity, self.tokens+dt*self.refill_rate)
        self.last=now
    def consume(self, n=1):
        with self.lock:
            self.refill()
            if self.tokens>=n:
                self.tokens-=n; return True
            return False
