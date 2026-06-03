import redis, json, time, csv
from collections import defaultdict
from token_bucket import TokenBucket
from config import *

r=redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
bucket=TokenBucket(BUCKET_CAPACITY, REFILL_RATE)

bin_counter=defaultdict(int)
last_alert=0

processed=0
dropped=0
bin_hits=0
last_stats=time.time()

def alert(msg):
    global last_alert
    now=time.time()
    if now-last_alert>=ALERT_COOLDOWN_SEC:
        print(f"🚨 ALERT: {msg}")
        last_alert=now

def detect_bin(tx):
    global bin_hits
    b=tx["card_bin"]
    bin_counter[b]+=1
    if bin_counter[b]>BIN_THRESHOLD:
        bin_hits+=1
        return True
    return False

def log_csv(p,d,bh):
    with open("stats.csv","a",newline="") as f:
        w=csv.writer(f)
        w.writerow([time.time(), p, d, bh])

def maybe_print_stats():
    global processed, dropped, bin_hits, last_stats
    now=time.time()
    if now-last_stats>=STATS_INTERVAL_SEC:
        print(f"📊 Stats | processed={processed} dropped={dropped} bin_flags={bin_hits}")
        log_csv(processed, dropped, bin_hits)
        processed=dropped=bin_hits=0
        last_stats=now

def process(tx):
    global processed
    processed+=1

def consume():
    print("Consumer started")
    while True:
        _, msg = r.brpop(QUEUE_NAME)
        tx=json.loads(msg)
        if detect_bin(tx):
            alert(f"BIN enumeration suspected on {tx['card_bin']}")
        elif bucket.consume():
            process(tx)
        else:
            global dropped
            dropped+=1
        maybe_print_stats()
