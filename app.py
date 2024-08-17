from flask import Flask, request, render_template, redirect, url_for, session
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy user data (still kept for profile route, can be removed if profile is also not needed)
users = {
    'testuser': {
        'password': 'testpass',
        'email': 'testuser@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'birthdate': '1990-01-01',
        'country': 'Testland'
    }
}

# Load and preprocess the dataset
def load_and_preprocess_data():
    df = pd.read_csv('movies.csv')
    
    # Replace values in the dataframe
    df = df.replace({'director_name': '-', 'director_professions': '-'}, 'Unknown')
    df = df.replace({'director_birthYear': ['-', '\\N'], 'director_deathYear': ['-', '\\N', 'alive']}, pd.NA)
    
    # Convert production_date to datetime
    df['production_date'] = pd.to_datetime(df['production_date'], errors='coerce')
    
    # Convert columns to numeric
    numeric_cols = ['runtime_minutes', 'movie_averageRating', 'movie_numerOfVotes', 'approval_Index',
                    'Production budget $', 'Domestic gross $', 'Worldwide gross $']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    # Drop unnecessary columns
    df = df.drop(columns=['director_birthYear', 'director_deathYear'])
    
    # Calculate profit columns
    df['domestic_profit'] = df['Domestic gross $'] - df['Production budget $']
    df['worldwide_profit'] = df['Worldwide gross $'] - df['Production budget $']
    
    # Split genres and expand into separate columns
    df['genres'] = df['genres'].str.split(',')
    genres_df = df['genres'].apply(pd.Series)
    genres_df.columns = [f'genre_{i+1}' for i in genres_df.columns]
    
    df = pd.concat([df, genres_df], axis=1)
    
    return df

df = load_and_preprocess_data()

@app.route('/')
def landing():
    major_genres = df['genre_1'].dropna().unique().tolist()[:5]  # Get top 5 genres
    return render_template('index.html', genres=major_genres)


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_type = request.args.get('search_type', 'Genre')
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    filtered_movies = df

    if search_type == 'Genre':
        filtered_movies = df[df['genres'].apply(lambda x: query in x)]
    elif search_type == 'Director':
        filtered_movies = df[df['director_name'].str.contains(query, case=False, na=False)]
    elif search_type == 'Rating':
        try:
            filtered_movies = df[df['movie_averageRating'] >= float(query)]
        except ValueError:
            return "Invalid rating format. Please enter a valid number."
    elif search_type == 'Production Date':
        try:
            query_date = datetime.strptime(query, '%Y-%m-%d')
            filtered_movies = df[df['production_date'].dt.date == query_date.date()]
        except ValueError:
            return "Invalid date format. Please use 'yyyy-mm-dd'."

    # Pagination logic
    per_page = 10
    total_pages = (len(filtered_movies) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_movies = filtered_movies.iloc[start:end]

    return render_template('recommendations.html', movies=paginated_movies.to_dict('records'), current_page=page, total_pages=total_pages, search_type=search_type, query=query)

@app.route('/genre/<genre_name>')
def genre_movies(genre_name):
    filtered_movies = df[df['genres'].apply(lambda x: genre_name in x)]
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = (len(filtered_movies) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_movies = filtered_movies.iloc[start:end]
    return render_template('recommendations.html', movies=paginated_movies.to_dict('records'), current_page=page, total_pages=total_pages, genre_name=genre_name)

@app.route('/recommendations')
def recommendations():
    # Sample movie recommendations
    movies = [
        {
            'movie_title': 'Avatar: The Way of Water',
            'director_name': 'James Cameron',
            'movie_averageRating': 7.8,
            'production_date': datetime.strptime('2022-12-09', '%Y-%m-%d'),
            'genres': ['Action', 'Adventure', 'Fantasy']
        },
        {
            'movie_title': 'Inception',
            'director_name': 'Christopher Nolan',
            'movie_averageRating': 8.8,
            'production_date': datetime.strptime('2010-07-16', '%Y-%m-%d'),
            'genres': ['Action', 'Sci-Fi', 'Thriller']
        }
        # Add more movies here
    ]
    return render_template('recommendations.html', movies=movies)

if __name__ == '__main__':
    app.run(debug=True)
