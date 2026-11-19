
import csv
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

# ==========================================
# CONFIGURATION
# ==========================================

LOG_DIR = Path("logs")
RESULTS_DIR = Path("results")

RESULTS_DIR.mkdir(exist_ok=True)

NORMAL_FILE = LOG_DIR / "receiver_timing_normal.csv"
WATERMARK_FILE = LOG_DIR / "receiver_timing_watermark.csv"

SENDER_WATERMARK_FILE = LOG_DIR / "sender_timing_watermark.csv"

# ==========================================
# READ RECEIVER CSV FILES
# ==========================================

def read_receiver_data(filename):

    with open(filename, "r", newline="") as file:

        rows = list(csv.DictReader(file))

    ipds = [
        float(row["measured_ipd_ms"])
        for row in rows
        if row["measured_ipd_ms"] != ""
    ]

    decoded_bits = [
        row["decoded_bit"]
        for row in rows
        if row["decoded_bit"] != ""
    ]

    return ipds, decoded_bits, len(rows)


normal_ipds, _, normal_packets = read_receiver_data(
    NORMAL_FILE
)

watermark_ipds, decoded_bits, watermark_packets = (
    read_receiver_data(WATERMARK_FILE)
)

# ==========================================
# READ SENDER WATERMARK DATA
# ==========================================

with open(SENDER_WATERMARK_FILE, "r", newline="") as file:

    sender_rows = list(csv.DictReader(file))

intended_bits = [
    row["intended_bit"]
    for row in sender_rows
    if row["intended_bit"] != ""
]

# ==========================================
# CALCULATE WATERMARK ACCURACY
# ==========================================

comparison_count = min(
    len(intended_bits),
    len(decoded_bits)
)

if comparison_count > 0:

    correct_bits = sum(
        intended_bits[i] == decoded_bits[i]
        for i in range(comparison_count)
    )

    accuracy = (
        correct_bits / comparison_count
    ) * 100

else:

    correct_bits = 0
    accuracy = 0

# ==========================================
# CALCULATE PERFORMANCE STATISTICS
# ==========================================

def calculate_statistics(ipds):

    return {
        "average_ipd_ms": statistics.mean(ipds),
        "minimum_ipd_ms": min(ipds),
        "maximum_ipd_ms": max(ipds),
        "standard_deviation_ms": statistics.pstdev(ipds),
        "number_of_intervals": len(ipds)
    }


normal_stats = calculate_statistics(normal_ipds)
watermark_stats = calculate_statistics(watermark_ipds)

# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n==========================================")
print("       CHAINPATROL PERFORMANCE ANALYSIS")
print("==========================================")

print("\nNORMAL MODE")

for metric, value in normal_stats.items():

    print(f"{metric}: {value:.3f}" if isinstance(value, float)
          else f"{metric}: {value}")

print("\nWATERMARK MODE")

for metric, value in watermark_stats.items():

    print(f"{metric}: {value:.3f}" if isinstance(value, float)
          else f"{metric}: {value}")

print("\nWATERMARK EXTRACTION ACCURACY")

print(f"Intended bits: {len(intended_bits)}")
print(f"Decoded bits: {len(decoded_bits)}")
print(f"Compared bits: {comparison_count}")
print(f"Correct bits: {correct_bits}")
print(f"Extraction accuracy: {accuracy:.2f}%")

# ==========================================
# SAVE PERFORMANCE SUMMARY
# ==========================================

summary_file = RESULTS_DIR / "performance_summary.csv"

with open(summary_file, "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "Mode",
        "Packets",
        "Intervals",
        "Average IPD (ms)",
        "Minimum IPD (ms)",
        "Maximum IPD (ms)",
        "IPD Standard Deviation (ms)"
    ])

    for mode, packets, stats in [
        ("Normal", normal_packets, normal_stats),
        ("Watermark", watermark_packets, watermark_stats)
    ]:

        writer.writerow([
            mode,
            packets,
            stats["number_of_intervals"],
            round(stats["average_ipd_ms"], 3),
            round(stats["minimum_ipd_ms"], 3),
            round(stats["maximum_ipd_ms"], 3),
            round(stats["standard_deviation_ms"], 3)
        ])

# ==========================================
# GRAPH 1: AVERAGE IPD COMPARISON
# ==========================================

plt.figure(figsize=(8, 5))

plt.bar(
    ["Normal", "Watermark"],
    [
        normal_stats["average_ipd_ms"],
        watermark_stats["average_ipd_ms"]
    ]
)

plt.title("Average IPD Comparison")
plt.xlabel("Transmission Mode")
plt.ylabel("Average IPD (ms)")
plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "average_ipd_comparison.png",
    dpi=300
)

plt.close()

# ==========================================
# GRAPH 2: IPD VARIATION
# ==========================================

plt.figure(figsize=(10, 5))

plt.plot(
    range(1, len(normal_ipds) + 1),
    normal_ipds,
    marker="o",
    label="Normal Mode"
)

plt.plot(
    range(1, len(watermark_ipds) + 1),
    watermark_ipds,
    marker="x",
    label="Watermark Mode"
)

plt.axhline(
    y=50,
    linestyle="--",
    label="Baseline IPD (50 ms)"
)

plt.title("Inter-Packet Delay Variation")
plt.xlabel("Packet Interval")
plt.ylabel("IPD (ms)")
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "ipd_variation.png",
    dpi=300
)

plt.close()

# ==========================================
# GRAPH 3: IPD STANDARD DEVIATION
# ==========================================

plt.figure(figsize=(8, 5))

plt.bar(
    ["Normal", "Watermark"],
    [
        normal_stats["standard_deviation_ms"],
        watermark_stats["standard_deviation_ms"]
    ]
)

plt.title("IPD Standard Deviation Comparison")
plt.xlabel("Transmission Mode")
plt.ylabel("Standard Deviation (ms)")
plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "ipd_standard_deviation.png",
    dpi=300
)

plt.close()

# ==========================================
# FINAL SUMMARY
# ==========================================

print("\n==========================================")
print("          ANALYSIS COMPLETED")
print("==========================================")

print(f"Summary: {summary_file}")

print("Graphs generated:")
print("1. results/average_ipd_comparison.png")
print("2. results/ipd_variation.png")
print("3. results/ipd_standard_deviation.png")

print("\nWatermark extraction accuracy:", f"{accuracy:.2f}%")

print("\n==========================================")
