import redis, json, time, uuid, random
from faker import Faker
from config import *
fake=Faker()
r=redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def gen_tx():
    return {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "amount": round(random.uniform(10,5000),2),
        "card_bin": str(random.randint(400000,400020))
    }

def produce(rate=4000):
    print(f"Producing {rate}/sec")
    while True:
        t0=time.time()
        for _ in range(rate):
            r.lpush(QUEUE_NAME, json.dumps(gen_tx()))
        dt=time.time()-t0
        if dt<1: time.sleep(1-dt)
