import requests
from bs4 import BeautifulSoup
import json
import time
import os
import threading
import queue

file_lock = threading.Lock()
last_processed_file = 'last_processed_subreddit.txt'

def convert_str_to_number(x):
    num_map = {'K': 1000, 'M': 1000000, 'B': 1000000000}
    if x.isdigit():
        return int(x)
    elif len(x) > 1 and x[-1] in num_map:
        return int(float(x[:-1]) * num_map.get(x[-1].upper(), 1))
    return 0

def scrape_subreddit(subreddit_queue, all_data_file):
    headers = {'User-Agent': 'Reddit Scraping Bot'}

    while True:
        subreddit = subreddit_queue.get()
        if subreddit is None:
            subreddit_queue.task_done()
            break  # Stopconditie

        url = f"https://old.reddit.com/r/{subreddit}/"
        posts = []
        page = 0
        while True:
            page += 1
            print(f"Scraping {subreddit}, Page {page}")
            try:
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                for post in soup.find_all('div', class_='thing'):
                    title = post.find('a', class_='title').text
                    post_url = post.find('a', class_='title')['href']
                    if post_url.startswith('/r/'):
                        post_url = f"https://www.reddit.com{post_url}"
                    
                    if not post_url.startswith("https://www.reddit.com") and not post_url.startswith("https://old.reddit.com"):
                        continue

                    author = post.find('a', class_='author').text if post.find('a', class_='author') else 'Anonymous'
                    score = convert_str_to_number(post.find('div', class_='score unvoted').text.strip(' points'))
                    comments = post.find('a', class_='comments').text.split()[0]
                    created_time = post.find('time')['datetime'] if post.find('time') else 'Unknown'
                    flair = post.find('span', class_='linkflairlabel').text if post.find('span', class_='linkflairlabel') else 'No Flair'
                    attachment = 'Yes' if post.find('a', class_='thumbnail') else 'No'

                    posts.append({
                        'title': title,
                        'url': post_url,
                        'author': author,
                        'subreddit': subreddit,
                        'upvotes': score,
                        'comments': comments,
                        'attachment': attachment,
                        'created_time': created_time,
                        'flair': flair
                    })

                next_button = soup.find('span', class_='next-button')
                url = next_button.find('a')['href'] if next_button else None
                if not url:
                    break
                time.sleep(2)

            except requests.RequestException as e:
                print(f"Fout bij het scrapen van {subreddit}: {e}")
                break

        append_to_json_file(posts, all_data_file)
        save_last_processed_subreddit(subreddit)
        subreddit_queue.task_done()

def read_subreddits(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def append_to_json_file(data, file_path):
    with file_lock:  # Gebruik het lock om thread-safe bestandsbewerkingen te garanderen
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            return

        with open(file_path, 'r+') as file:
            try:
                file_data = json.load(file)
                file_data.extend(data)
                file.seek(0)
                json.dump(file_data, file, indent=4)
            except json.JSONDecodeError as e:
                print(f"Fout bij het lezen van JSON-bestand: {e}")

def save_last_processed_subreddit(subreddit):
    with open(last_processed_file, 'w') as file:
        file.write(subreddit)

def read_last_processed_subreddit():
    if os.path.isfile(last_processed_file):
        with open(last_processed_file, 'r') as file:
            return file.read().strip()
    return None

def main():
    subreddits = read_subreddits('all2.txt')
    all_data_file = 'Allsubs.json'
    last_processed = read_last_processed_subreddit()

    if last_processed in subreddits:
        last_index = subreddits.index(last_processed)
        subreddits = subreddits[last_index + 1:]  # Hervat na de laatste verwerkte subreddit

    subreddit_queue = queue.Queue(maxsize=10)

    threads = []
    for _ in range(20):  # Start met 10 threads
        thread = threading.Thread(target=scrape_subreddit, args=(subreddit_queue, all_data_file))
        thread.start()
        threads.append(thread)

    for subreddit in subreddits:
        subreddit_queue.put(subreddit)

    for _ in range(10):  # Stuur stopsignalen naar threads
        subreddit_queue.put(None)

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
