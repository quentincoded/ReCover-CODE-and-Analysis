import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import textwrap # Import textwrap for wrapping long labels
from matplotlib.patches import Patch # For custom legend icons

# --- Configuration ---
# IMPORTANT: Update this to your CSV file name!
# Ensure your CSV is in the same directory as this script, or provide the full path.
csv_file_path = 'DataAnalysis/IndividualQuestions/Book1.csv'

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

# Add a 'Respondent' column (e.g., 'Patient 1', 'Patient 2', etc.)
# This assigns a unique identifier to each row (individual respondent)
df_raw['Respondent'] = ['Patient ' + str(i + 1) for i in range(len(df_raw))]

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
# This step removes individual missing responses, but we ensure the question category still exists below.
df_long = df_long.dropna(subset=['Response_Score'])

# FIX: Ensure the order of questions on the x-axis includes ALL likert_questions_cols
# This guarantees that all questions will have a tick on the x-axis, even if they have no data.
ordered_questions_text = likert_questions_cols
df_long['Question'] = pd.Categorical(df_long['Question'], categories=ordered_questions_text, ordered=True)

# Calculate the overall average score for each question across all respondents
# Added observed=False to silence FutureWarning
df_overall_averages = df_long.groupby('Question', observed=False)['Response_Score'].mean().reset_index()
df_overall_averages.columns = ['Question', 'Overall_Average_Score']

# Ensure the average DataFrame also uses the same categorical order for questions
df_overall_averages['Question'] = pd.Categorical(
    df_overall_averages['Question'],
    categories=ordered_questions_text,
    ordered=True
)

# --- Define specific questions to color blue for X-axis labels ---
# Assuming 'row 8' and 'row 9' refer to the 8th and 9th question in the ordered list (0-indexed)
# These are the indices of the questions whose labels will be blue
blue_label_indices = []
if len(ordered_questions_text) >= 8: # 8th question (index 7)
    blue_label_indices.append(7)
if len(ordered_questions_text) >= 9: # 9th question (index 8)
    blue_label_indices.append(8)

print(f"X-axis labels to be colored blue (indices): {blue_label_indices}")

# --- Define questions to be de-emphasized/hidden ---
# User requested columns 1, 2, 5, 6, 7, 8, 11 to be invisible
# Convert these to 0-indexed positions in ordered_questions_text
de_emphasized_question_indices = [idx for idx, q_name in enumerate(ordered_questions_text)
                                  if idx in [0, 1, 4, 5, 6, 7, 10]] # Q1, Q2, Q5, Q6, Q7, Q8, Q11

# Get the actual names of the de-emphasized questions for direct comparison
de_emphasized_question_names = [ordered_questions_text[i] for i in de_emphasized_question_indices]

print(f"Questions to be de-emphasized (indices): {de_emphasized_question_indices}")
print(f"Questions to be de-emphasized (names): {de_emphasized_question_names}")


# --- 3. Plotting the data ---
# Increased figure size slightly for better layout
plt.figure(figsize=(20, 10))
ax = plt.gca() # Get current axes for later manipulation

# --- Color Customization ---
# Use a named seaborn palette for the individual bars (reverting to full pastel palette)
individual_bar_palette = 'plasma'

# Color for the overall average scatter point
overall_average_color = 'red'
# --- End Color Customization ---


# Create the grouped bar plot
# Use the default pastel palette for all respondents
barplot_obj = sns.barplot(
    data=df_long,
    x='Question',
    y='Response_Score',
    hue='Respondent',
    palette=individual_bar_palette, # Apply the chosen palette for individual bars
    edgecolor='gray',
    linewidth=0.5,
    alpha=0.8, # Initial alpha for all bars
    errorbar=None,
    ax=ax # Assign to the pre-obtained axes
)

# --- Make bars transparent for de-emphasized questions ---
# Get the x-tick locations (numerical positions of each question category)
x_tick_locations = ax.get_xticks()

for bar_patch in barplot_obj.patches:
    # Calculate the center of the bar
    bar_center_x = bar_patch.get_x() + bar_patch.get_width() / 2

    # Find the index of the closest x-tick location
    # This maps the bar's position to its corresponding question category index
    closest_tick_index = (np.abs(x_tick_locations - bar_center_x)).argmin()
    
    # Get the question name associated with that closest tick
    question_name_for_bar = ordered_questions_text[closest_tick_index]

    if question_name_for_bar in de_emphasized_question_names:
        bar_patch.set_alpha(0.05) # Make very transparent
# --- End bar transparency adjustment ---


# Simpler way to handle scatterplot transparency: filter the data before plotting
# Create a filtered DataFrame for only the highlighted average points
df_highlighted_averages = df_overall_averages[~df_overall_averages['Question'].isin(de_emphasized_question_names)].copy()
df_de_emphasized_averages = df_overall_averages[df_overall_averages['Question'].isin(de_emphasized_question_names)].copy()

# Plot highlighted averages
sns.scatterplot(
    data=df_highlighted_averages,
    x='Question',
    y='Overall_Average_Score',
    color=overall_average_color,
    marker='D',
    s=200,
    label='Overall Average',
    zorder=5,
    linewidth=1,
    edgecolor='black',
    ax=ax
)

# Plot de-emphasized averages with low alpha
sns.scatterplot(
    data=df_de_emphasized_averages,
    x='Question',
    y='Overall_Average_Score',
    color=overall_average_color,
    marker='D',
    s=200,
    label='_nolegend_', # Hide from legend
    zorder=5,
    linewidth=1,
    edgecolor='black',
    alpha=0.05, # Very transparent
    ax=ax
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

plt.yticks(list(likert_labels.keys()), list(likert_labels.values()))
plt.ylabel('Likert Scale Response (1-7)', fontsize=12)
plt.ylim(0.5, 7.5)

# --- X-axis label wrapping and rotation ---
max_width_question_label = 20
wrapped_labels = [textwrap.fill(label, max_width_question_label) for label in ordered_questions_text]

# Set X-axis ticks and labels with wrapping and rotation
plt.xticks(ticks=range(len(ordered_questions_text)), labels=wrapped_labels, rotation=45, ha='right', fontsize=10)

# --- Color X-axis labels based on `blue_label_indices` and `de_emphasized_question_indices` ---
for i, tick_label in enumerate(ax.get_xticklabels()):
    if i in blue_label_indices:
        tick_label.set_color('blue')
    elif ordered_questions_text[i] in de_emphasized_question_names: # Use name for consistency
        tick_label.set_color('lightgrey') # Light grey for de-emphasized
    else:
        tick_label.set_color('black') # Default black for others (highlighted)
# --- End X-axis label wrapping and rotation ---


# Add titles
plt.title('Individual Responses per Respondent and Overall Average per Question', fontsize=22, pad=20)
# plt.suptitle('Questionnaire Results - Individual Bars with Overall Average Overlay', fontsize=20, y=1.03)

# --- Legend Handling (Combined) ---
# Get all handles and labels from the current plot
handles, labels = ax.get_legend_handles_labels()

# Create a dictionary to map labels to their handles for easier sorting
label_handle_map = dict(zip(labels, handles))

# Define the desired order of labels in the legend: 'Overall Average' first, then 'Patient 1', 'Patient 2', etc.
desired_label_order = ['Overall Average'] + sorted([l for l in labels if l.startswith('Patient')])

# Create new lists of handles and labels in the desired order
ordered_handles = [label_handle_map[label] for label in desired_label_order if label in label_handle_map]
ordered_labels = [label for label in desired_label_order if label in label_handle_map]

# Create a single legend with the combined and reordered items
legend1 = ax.legend(ordered_handles, ordered_labels, title='Metrics', bbox_to_anchor=(1.01, 1), loc='upper left')
ax.add_artist(legend1) # Add this legend back to the axes to prevent it from being overwritten

# --- Add new legend for color interpretation (referring to text color) ---
# Create custom legend handles for color interpretation with square icons
color_legend_handles = [
    # Patch for 'High = Good' (black text)
    Patch(facecolor='black', edgecolor='black', label='High = Good (Black Text)'),
    # Patch for 'Low = Good' (blue text)
    Patch(facecolor='blue', edgecolor='black', label='Low = Good (Blue Text)'),
    # Patch for 'De-emphasized' (light grey text)
    # Patch(facecolor='lightgrey', edgecolor='black', label='De-emphasized (Grey Text)')
]

legend2 = ax.legend(handles=color_legend_handles,
                   title='Interpretation of Scores',
                   bbox_to_anchor=(1.01, -0.1), # Position this legend below the first one
                   loc='center left',
                   frameon=True)
ax.add_artist(legend2)


# Add a subtle horizontal grid
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Adjust layout to prevent labels from being cut off, making space for the legend(s)
# Increased right margin more to accommodate two legends
plt.tight_layout(rect=[0, 0.05, 0.85, 0.95])

plt.show()
