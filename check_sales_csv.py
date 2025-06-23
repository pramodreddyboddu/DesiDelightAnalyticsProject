import pandas as pd
import os

# Check the sales CSV file
csv_file = 'upload/LineItemsExport-20250501_0000_CDT-20250531_2359_CDT.csv'

print(f"File size: {os.path.getsize(csv_file) / (1024*1024):.2f} MB")

# Read just the first few rows to check structure
df_sample = pd.read_csv(csv_file, nrows=5)
print(f"Sample data shape: {df_sample.shape}")
print("Columns:", df_sample.columns.tolist())

# Count total rows (this might take a while for large files)
print("Counting total rows...")
with open(csv_file, 'r') as f:
    line_count = sum(1 for line in f) - 1  # Subtract 1 for header
print(f"Total rows: {line_count}") 