import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

API_URL = "https://en.wikipedia.org/w/api.php"

ARTICLES = [
    "Climate change",
    "Bitcoin",
    "Python (programming language)"
]

HEADERS = {
    'User-Agent': 'DataAnalysisProject/1.0 (contact@example.com)'
}

def fetch_revisions(title, limit=500):
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "timestamp|user|comment|size",
        "rvlimit": limit,
        "format": "json"
    }
    
    response = requests.get(API_URL, headers=HEADERS, params=params)
    data = response.json()
    
    pages = data['query']['pages']
    page_id = list(pages.keys())[0]
    
    if page_id == "-1":
        print(f"Page '{title}' not found.")
        return pd.DataFrame()
        
    revisions = pages[page_id].get('revisions', [])
    df = pd.DataFrame(revisions)
    df['page_title'] = title
    return df

print("Fetching Wikipedia revision history...")
all_data = []

for title in ARTICLES:
    print(f" -> Fetching {title}...")
    df_revs = fetch_revisions(title, limit=500)
    if not df_revs.empty:
        all_data.append(df_revs)

df = pd.concat(all_data, ignore_index=True)

df['timestamp'] = pd.to_datetime(df['timestamp'])
df['comment'] = df['comment'].fillna('')

revert_keywords = ['revert', 'undid', 'undo', 'rv', 'vandalism']
df['is_revert'] = df['comment'].str.lower().apply(
    lambda c: any(kw in c for kw in revert_keywords)
)

summary = df.groupby('page_title').agg(
    total_edits=('timestamp', 'count'),
    unique_editors=('user', 'nunique'),
    total_reverts=('is_revert', 'sum')
).reset_index()

summary['revert_rate'] = summary['total_reverts'] / summary['total_edits']
summary['editor_diversity'] = summary['unique_editors'] / summary['total_edits']
summary['controversy_score'] = (summary['revert_rate'] * summary['editor_diversity'] * 100).round(2)

print("\n--- CONTROVERSY INDEX SUMMARY ---")
print(summary[['page_title', 'total_edits', 'unique_editors', 'total_reverts', 'controversy_score']])

# Save summary dataset to a CSV file
os.makedirs('data', exist_ok=True)
summary.to_csv('data/controversy_summary.csv', index=False)
print("Data exported successfully to 'data/controversy_summary.csv'")

os.makedirs('assets', exist_ok=True)
plt.figure(figsize=(9, 5))
sns.set_theme(style="whitegrid")

ax = sns.barplot(
    data=summary,
    x='page_title',
    y='controversy_score',
    palette='Reds_d'
)

plt.title('Wikipedia Controversy Index Comparison', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Article Title', fontsize=11)
plt.ylabel('Calculated Controversy Score', fontsize=11)

for p in ax.patches:
    ax.annotate(f"{p.get_height():.2f}",
                (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center', xytext=(0, 8),
                textcoords='offset points', fontweight='bold')

plt.tight_layout()
plt.savefig('assets/controversy_comparison.png', dpi=300)
print("\nPlot saved successfully to 'assets/controversy_comparison.png'")