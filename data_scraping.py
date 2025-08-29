import os
import time
import glob
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Path for Cromedriver
path = "C:/Users/workstation/Downloads/chromedriver-win64/chromedriver.exe"
service = Service(executable_path=path)
options = Options()
driver = webdriver.Chrome(service=service, options=options)

# Website URL
website = "https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31&genres={genre}&sort=alpha,asc"
wait = WebDriverWait(driver, 10)

genres = [
    'action', 'adventure', 'animation', 'biography', 'comedy', 'crime',
    'documentary', 'drama', 'family', 'fantasy', 'history',
    'horror', 'music', 'musical', 'mystery', 'romance', 'sci-fi',
    'sport', 'thriller', 'war', 'western'
]

def load_all_movies():
    total_loaded = 0
    while True:
        try:
            # Scroll down to the button using JavaScript
            load_more_btn = wait.until(EC.presence_of_element_located((By.XPATH, '//button[@class="ipc-btn ipc-btn--single-padding ipc-btn--center-align-content ipc-btn--default-height ipc-btn--core-base ipc-btn--theme-base ipc-btn--button-radius ipc-btn--on-accent2 ipc-text-button ipc-see-more__button"]')))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_btn)
            time.sleep(1)  # wait for scroll animation
        
            driver.execute_script("arguments[0].click();", load_more_btn)
            total_loaded += 50
            print(f"'Load more' clicked... ({total_loaded} movies loaded)")
            time.sleep(2)  # give time to load content
    
        except TimeoutException:
            print("No more '50 more' button found.")
            break

def scrape_genre(genre):
    print(f"Scraping genre: {genre}")
    url = website.format(genre=genre)
    driver.get(url)
    time.sleep(3)

    load_all_movies()

    movie_blocks = driver.find_elements(By.XPATH, '//li[@class="ipc-metadata-list-summary-item"]')
            
    data = []
                
    for movie in movie_blocks:
        title = storyline = "N/A"
        
        try:
            raw_title = movie.find_element(By.XPATH, './/div[@class = "ipc-title ipc-title--base ipc-title--title ipc-title--title--reduced ipc-title-link-no-icon ipc-title--on-textPrimary sc-3cb45114-2 gReSCf dli-title with-margin"]/a/h3').text
            title = raw_title.split('. ', 1)[1] if '. ' in raw_title else raw_title
        except:
            pass
            
        try:
            storyline = movie.find_element(By.XPATH, './/div[@class = "ipc-html-content-inner-div"]').text
        except:
            pass

        data.append({'Title' : title, 'Storyline' : storyline})

    df = pd.DataFrame(data).drop_duplicates()

    # Save to CSV
    output_dir = "imdb_data"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"IMDB_Movie_Data_{genre}.csv"
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} movies to {filepath}")

# Scraping Data    
for genre in genres:
    try:
        scrape_genre(genre)
    except Exception as e:
        print(f"Error scraping {genre}: {e}")
        continue

driver.quit()
print("Scraping complete")

# Merging CSV files
files = glob.glob("C:/Users/workstation/Downloads/Movie Recomendation/imdb_data/IMDB_Movie_Data_*")
merged_csv = pd.concat([pd.read_csv(file, usecols = ['Title', 'Storyline']) for file in files])
merged_csv.drop_duplicates(inplace=True)
combined_df = merged_csv.groupby('Title', as_index=False).agg({
    'Storyline' : 'first'
})
# Replace empty or NaN storylines with "N/A"
combined_df['Storyline'] = combined_df['Storyline'].replace({pd.NA: "N/A", "": "N/A"}).fillna("N/A")
combined_df.to_csv('IMDB_Movies_Data.csv', index=False, encoding='utf-8-sig')
print(f'{len(files)} csv files merged')