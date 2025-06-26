import pandas as pd

# Read the Items sheet specifically
df = pd.read_excel('upload/inventory-export-v2.xlsx', sheet_name='Items', header=None)

print("Items sheet structure analysis:")
print("=" * 50)

# Print the full header row
print("Header row (row 0):")
print(df.iloc[0].tolist())

# Look at the first 20 rows to understand the structure
for i in range(min(20, len(df))):
    row_data = df.iloc[i]
    print(f"Row {i}: {row_data.iloc[0] if not pd.isna(row_data.iloc[0]) else 'EMPTY'}")

print("\n" + "=" * 50)
print("Looking for rows containing 'item name' or similar:")

# Search for rows that might contain headers
for i in range(min(50, len(df))):
    row_data = df.iloc[i]
    row_str = str(row_data.iloc[0]).lower() if not pd.isna(row_data.iloc[0]) else ""
    if 'item' in row_str and 'name' in row_str:
        print(f"Found potential header at row {i}: {row_data.iloc[0]}")
        print(f"Full row data: {row_data.tolist()}")
        break

# Also check all sheets
xl_file = pd.ExcelFile('upload/inventory-export-v2.xlsx')
print(f"\nSheets in the file: {xl_file.sheet_names}") 