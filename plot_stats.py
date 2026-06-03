import csv, matplotlib.pyplot as plt
ts=[]; p=[]; d=[]; b=[]
with open("stats.csv") as f:
    r=csv.reader(f)
    for row in r:
        ts.append(float(row[0])); p.append(int(row[1])); d.append(int(row[2])); b.append(int(row[3]))
plt.plot(ts, p, label="processed")
plt.plot(ts, d, label="dropped")
plt.plot(ts, b, label="bin_flags")
plt.legend(); plt.xlabel("time"); plt.ylabel("count")
plt.title("Traffic & BIN Detection Trends")
plt.show()
