
# ChainPatrol - IPD Calculator

# Packet arrival timestamps in seconds
timestamps = [0.000, 0.050, 0.110, 0.160, 0.230]

# Empty list to store calculated IPDs
ipds = []

# Calculate the delay between consecutive packets
for i in range(1, len(timestamps)):

    ipd = timestamps[i] - timestamps[i - 1]

    # Convert seconds into milliseconds
    ipd_ms = ipd * 1000

    ipds.append(ipd_ms)

    print(f"Packet {i} -> Packet {i + 1}: {ipd_ms:.2f} ms")

# Calculate average IPD
average_ipd = sum(ipds) / len(ipds)

print("--------------------------------")
print(f"Average IPD: {average_ipd:.2f} ms")
