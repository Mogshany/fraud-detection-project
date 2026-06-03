import threading
from producer import produce
from consumer import consume

if __name__=="__main__":
    t1=threading.Thread(target=produce, args=(6000,))
    t2=threading.Thread(target=consume)
    t1.start(); t2.start()
    t1.join(); t2.join()
