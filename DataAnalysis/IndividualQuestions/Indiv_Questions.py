import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import textwrap # Import textwrap for wrapping long labels

# --- Configuration ---
# IMPORTANT: Update this to your CSV file name!
# Ensure your CSV is in the same directory as this script, or provide the full path.
csv_file_path = 'DataAnalysis/IndividualQuestions/Book2.csv'

# IMPORTANT: List the exact column name(s) from your CSV that are NOT Likert scale responses.
# If ALL columns are Likert scale questions, leave this list empty: []
non_likert_cols_to_exclude = ['Which mode did you prefer?'] # Example: ['Participant ID', 'Timestamp']


# 1. Load Data from CSV
try:
    print(f"Attempting to load data from {csv_file_path}...")
    # Using semicolon as delimiter, as indicated by previous error
    df_raw = pd.read_csv(csv_file_path, sep=';')
    print(f"Successfully loaded data from {csv_file_path}")
    print("Raw data head:")
    print(df_raw.head())
    print("\nColumns in your CSV:")
    print(df_raw.columns.tolist())
except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found.")
    print("Please make sure the CSV file is in the same directory as your script, or provide the full path.")
    exit()
except pd.errors.EmptyDataError:
    print(f"Error: The file '{csv_file_path}' is empty.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred while reading the CSV: {e}")
    print("This might be due to an incorrect delimiter or corrupted file format.")
    print("Please check your CSV file content and ensure it's valid.")
    exit()

# 2. Prepare Data for Plotting (Long Format)
print("\nPreparing data for plotting...")

# Identify Likert scale questions by excluding non-Likert columns
likert_questions_cols = [
    col for col in df_raw.columns
    if col not in non_likert_cols_to_exclude
]

# Add a 'Respondent' column (e.g., 'Guy 1', 'Guy 2', etc.)
# This assigns a unique identifier to each row (individual respondent)
df_raw['Respondent'] = ['Guy ' + str(i + 1) for i in range(len(df_raw))]

# Convert only identified Likert columns to numeric, coercing errors (e.g., empty strings) to NaN
for col in likert_questions_cols:
    df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')

# Melt the DataFrame to long format
# This transforms question columns into rows, making it suitable for grouped bar plots
df_long = df_raw.melt(
    id_vars=['Respondent'], # Keep 'Respondent' as an ID column
    value_vars=likert_questions_cols, # These are the columns to "unpivot"
    var_name='Question', # New column for question names (from CSV headers)
    value_name='Response_Score' # New column for response scores
)

# Remove rows where the 'Response_Score' is NaN (e.g., missing data for a specific question/respondent)
df_long = df_long.dropna(subset=['Response_Score'])

# Ensure the order of questions on the x-axis is maintained as they appeared in the CSV
# This prevents alphabetical sorting and keeps your intended question order.
ordered_questions_text = [q for q in likert_questions_cols if q in df_long['Question'].unique()]
df_long['Question'] = pd.Categorical(df_long['Question'], categories=ordered_questions_text, ordered=True)

# Calculate the overall average score for each question across all respondents
# FIX: Added observed=False to silence FutureWarning
df_overall_averages = df_long.groupby('Question', observed=False)['Response_Score'].mean().reset_index()
df_overall_averages.columns = ['Question', 'Overall_Average_Score']

# Ensure the average DataFrame also uses the same categorical order for questions
df_overall_averages['Question'] = pd.Categorical(
    df_overall_averages['Question'],
    categories=ordered_questions_text,
    ordered=True
)


# --- 3. Plotting the data ---
# FIX: Increased figure size slightly for better layout
plt.figure(figsize=(20, 9))

# Create the grouped bar plot
# Each 'Question' gets a group of bars, and each bar within the group represents a 'Respondent'
sns.barplot(
    data=df_long,
    x='Question',
    y='Response_Score',
    hue='Respondent', # This creates a separate bar for each 'Respondent'
    palette='muted', # A nice pastel color palette for individual bars
    edgecolor='gray', # Add a subtle edge to bars
    linewidth=0.5,
    alpha=0.8, # Make bars slightly transparent
    errorbar=None # Do not show error bars for individual responses
)

# Overlay the overall average points as a scatter plot
sns.scatterplot(
    data=df_overall_averages,
    x='Question',
    y='Overall_Average_Score',
    color='red',        # Set color to red
    marker='D',         # Use diamond marker
    s=200,              # Size of the diamond marker
    label='Overall Average', # Label for the legend
    zorder=5,           # Ensure scatter points are on top of bar plots
    linewidth=1,        # Add a border to the diamond
    edgecolor='black'   # Color of the diamond border
)


# Customize the Y-axis labels to show Likert scale terms (1-7)
likert_labels = {
    1: 'Strongly Disagree',
    2: 'Disagree',
    3: 'Slightly Disagree',
    4: 'Neutral',
    5: 'Slightly Agree',
    6: 'Agree',
    7: 'Strongly Agree'
}

# Set Y-axis ticks and labels
plt.yticks(list(likert_labels.keys()), list(likert_labels.values()))
plt.ylabel('Likert Scale Response (1-7)', fontsize=12)
plt.ylim(0.5, 7.5) # Set limits to ensure all labels are visible

# --- X-axis label wrapping and rotation ---
# Adjust this value to control how wide each wrapped line of text can be
max_width_question_label = 20
wrapped_labels = [textwrap.fill(label, max_width_question_label) for label in ordered_questions_text]

# Set X-axis ticks and labels with wrapping and rotation
plt.xticks(ticks=range(len(ordered_questions_text)), labels=wrapped_labels, rotation=45, ha='right', fontsize=10)
# --- End X-axis label wrapping and rotation ---


# Add titles
plt.title('Responses to individual device related questions', fontsize=16, pad=20)
# FIX: Adjusted y-position of suptitle to ensure it's within bounds
# plt.suptitle('Questionnaire Results - Individual Bars with Overall Average Overlay', fontsize=20, y=1.03)

# --- Legend Handling ---
# Get all handles and labels from the current plot
handles, labels = plt.gca().get_legend_handles_labels()

# Create a dictionary to map labels to their handles for easier sorting
label_handle_map = dict(zip(labels, handles))

# Define the desired order of labels in the legend
# 'Overall Average' first, then 'Guy 1', 'Guy 2', etc.
desired_label_order = ['Overall Average'] + sorted([l for l in labels if l.startswith('Guy')])

# Create new lists of handles and labels in the desired order
ordered_handles = [label_handle_map[label] for label in desired_label_order if label in label_handle_map]
ordered_labels = [label for label in desired_label_order if label in label_handle_map]

# Create a single legend with the combined and reordered items
plt.legend(ordered_handles, ordered_labels, title='Metrics', bbox_to_anchor=(1.05, 1), loc='upper left')
# --- End Legend Handling ---


# Add a subtle horizontal grid
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Adjust layout to prevent labels from being cut off, making space for the legend(s)
# FIX: Increased right margin slightly to ensure legends fit
plt.tight_layout(rect=[0, 0.05, 0.88, 0.95])

plt.show()
