#!/usr/bin/env python3
import pandas as pd

# Read CSV file
input_file_path = 'evict-btree-trace.csv'  # Replace 'your_input_file.csv' with the actual filename
df = pd.read_csv(input_file_path)

# Select the 2nd and 6th columns
selected_columns = df.iloc[:, [1, 5]]  # Assuming columns are zero-indexed

selected_columns.columns =  ['node_address', 'parent_address'];

# Write the result to a new CSV file
output_file_path = 'btree-vis-output.csv'  # Replace 'output_file.csv' with the desired output filename
selected_columns.to_csv(output_file_path, header=True, index=False)
