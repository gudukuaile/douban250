from flask import Flask, jsonify, render_template
import pandas as pd

app = Flask(__name__)
df_movies = None

def load_data():
    global df_movies
    try:
        df_movies = pd.read_excel("豆瓣电影Top250.xls")
        print("Data loaded successfully.")
    except FileNotFoundError:
        print("Error: 豆瓣电影Top250.xls not found.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/data/movies_by_year')
def movies_by_year_data():
    if df_movies is None:
        return jsonify({"error": "Data not loaded"}), 500

    if '年份' not in df_movies.columns:
        return jsonify({"error": "Required column missing: '年份'"}), 400

    movies_by_year = df_movies.groupby('年份').size().reset_index(name='counts')
    data = {
        'years': movies_by_year['年份'].tolist(),
        'counts': movies_by_year['counts'].tolist()
    }
    return jsonify(data)

@app.route('/charts/movies_by_year')
def movies_by_year_chart():
    return render_template('movies_by_year.html')

@app.route('/data/movies_by_country')
def movies_by_country_data():
    if df_movies is None:
        return jsonify({"error": "Data not loaded"}), 500

    # Process '国家' column - take the first country if multiple are listed
    # Ensure '国家' column exists and is of string type before attempting string operations
    if '国家' not in df_movies.columns:
        return jsonify({"error": "Required column missing: '国家'"}), 400

    # Create a copy to avoid SettingWithCopyWarning
    df_copy = df_movies.copy()
    df_copy['processed_country'] = df_copy['国家'].astype(str).apply(lambda x: x.split('/')[0].strip())

    movies_by_country = df_copy.groupby('processed_country').size().reset_index(name='counts')

    # Sort by counts descending and take top N (e.g., top 10) for better visualization
    top_n = 10
    movies_by_country = movies_by_country.sort_values(by='counts', ascending=False).head(top_n)

    data = {
        'countries': movies_by_country['processed_country'].tolist(),
        'counts': movies_by_country['counts'].tolist()
    }
    return jsonify(data)

@app.route('/charts/movies_by_country')
def movies_by_country_chart():
    return render_template('movies_by_country.html')

@app.route('/data/movies_by_genre')
def movies_by_genre_data():
    if df_movies is None:
        return jsonify({"error": "Data not loaded"}), 500

    if '类型' not in df_movies.columns:
        return jsonify({"error": "Required column missing: '类型'"}), 400

    genre_counts = {}
    for genres_str in df_movies['类型'].astype(str):
        genres_list = genres_str.split('/')
        for genre in genres_list:
            genre = genre.strip()
            if genre: # Ensure non-empty genre string
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Sort genres by count in descending order
    sorted_genres = sorted(genre_counts.items(), key=lambda item: item[1], reverse=True)

    # Prepare data for Chart.js
    # For horizontal bar chart, labels (genres) are on Y-axis, data (counts) on X-axis
    data = {
        'genres': [item[0] for item in sorted_genres],
        'counts': [item[1] for item in sorted_genres]
    }
    return jsonify(data)

@app.route('/charts/movies_by_genre')
def movies_by_genre_chart():
    return render_template('movies_by_genre.html')

@app.route('/data/avg_rating_by_year')
def avg_rating_by_year_data():
    if df_movies is None:
        return jsonify({"error": "Data not loaded"}), 500

    if '年份' not in df_movies.columns:
        return jsonify({"error": "Required column missing: '年份'"}), 400
    if '评分' not in df_movies.columns:
        return jsonify({"error": "Required column missing: '评分'"}), 400

    # Create a copy to avoid modifying the original DataFrame
    df_copy = df_movies.copy()

    # Convert '评分' to numeric, coercing errors to NaN
    df_copy['评分'] = pd.to_numeric(df_copy['评分'], errors='coerce')

    # Drop rows where '评分' became NaN after conversion, if any
    df_copy.dropna(subset=['评分'], inplace=True)

    # Group by '年份' and calculate mean of '评分', then sort by '年份'
    avg_rating_year = df_copy.groupby('年份')['评分'].mean().sort_index()

    data = {
        'years': avg_rating_year.index.tolist(),
        'average_ratings': avg_rating_year.values.tolist()
    }
    return jsonify(data)

@app.route('/charts/avg_rating_by_year')
def avg_rating_by_year_chart():
    return render_template('avg_rating_by_year.html')

@app.route('/data/rating_distribution')
def rating_distribution_data():
    if df_movies is None:
        return jsonify({"error": "Data not loaded"}), 500

    if '评分' not in df_movies.columns:
        return jsonify({"error": "Required column missing: '评分'"}), 400

    df_copy = df_movies.copy()
    df_copy['评分'] = pd.to_numeric(df_copy['评分'], errors='coerce')
    df_copy.dropna(subset=['评分'], inplace=True)

    # Define rating brackets
    # Bins could be [7.5, 8.0, 8.5, 9.0, 9.5, 10.0] to ensure 9.5+ is captured.
    # Max rating in Top250 is likely high but might not exceed 9.7 or 9.8. Let's check data range or set a reasonable upper limit.
    # Assuming max rating is <= 10.
    min_rating = df_copy['评分'].min()
    max_rating = df_copy['评分'].max()

    # Let's make bins dynamic based on data, but for this task, fixed bins are requested.
    # Bins: (x, y] interval notation.
    # To include 9.5 and above, the last bin should extend to a value > max_rating or use right=False and include max_rating.
    # Let's use: [7.5-8.0), [8.0-8.5), [8.5-9.0), [9.0-9.5), [9.5, max_rating+0.1) to make it inclusive of 9.5
    # Simpler: define edges and labels
    bins = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, max_rating + 0.01] # max_rating + 0.01 to ensure max_rating is included
    labels = ['7.0-7.49', '7.5-7.99', '8.0-8.49', '8.5-8.99', '9.0-9.49', f'9.5-{max_rating}']

    if min_rating < 7.0 : # Adjust if there are movies rated below 7.0
        bins.insert(0, min_rating - 0.01)
        labels.insert(0, f'{min_rating}-{bins[1]-0.01}')


    df_copy['rating_bracket'] = pd.cut(df_copy['评分'], bins=bins, labels=labels, right=False) # right=False means [bin, next_bin)

    rating_counts = df_copy['rating_bracket'].value_counts().sort_index()

    data = {
        'rating_brackets': rating_counts.index.astype(str).tolist(), # Convert Interval to string
        'counts': rating_counts.values.tolist()
    }
    return jsonify(data)

@app.route('/charts/rating_distribution')
def rating_distribution_chart():
    return render_template('rating_distribution.html')

if __name__ == '__main__':
    load_data()
    app.run(debug=True)
