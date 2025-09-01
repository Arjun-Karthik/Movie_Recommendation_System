# 🎬 Movie Recommendation System

⚙️ Workflow
1. Data Scraping
   
    - Uses Selenium to scrape IMDb 2024 movie data.
    - Extracted fields:
        - Movie Name
        - Storyline (Plot Summary)
    - Data is stored in IMDB_Movies_Data.csv with columns:
        - Movie Name
        - Storyline

2. Data Cleaning & Preprocessing

    - Remove stopwords, punctuation, and special characters.
    - Tokenize text for analysis.
    - Convert text to vectors using TF-IDF or Count Vectorizer.
