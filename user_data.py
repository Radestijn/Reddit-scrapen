import json
import os

def load_all_posts(file_path):
    if not os.path.exists(file_path):
        print(f"Bestand niet gevonden: {file_path}")
        return []

    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Fout bij het laden van JSON uit {file_path}: {e}")
        return []

def aggregate_user_data(posts):
    user_data = {}

    for post in posts:
        author = post.get('author')
        subreddit = post.get('subreddit')

        if not author or not subreddit:
            continue

        if author not in user_data:
            user_data[author] = {
                'posts': 0,
                'subreddits': set(),
                'url': f"https://www.reddit.com/user/{author}"
            }

        user_data[author]['posts'] += 1
        user_data[author]['subreddits'].add(subreddit)

    for user in user_data:
        user_data[user]['subreddits'] = list(user_data[user]['subreddits'])

    return user_data

def main():
    all_posts_file = 'Allsubs.json'
    all_posts = load_all_posts(all_posts_file)

    if not all_posts:
        print("Geen posts geladen, script wordt afgesloten.")
        return

    user_data = aggregate_user_data(all_posts)

    with open('User_data.json', 'w') as file:
        json.dump(user_data, file, indent=4)
    print("Gebruikersgegevens opgeslagen in User_data.json")

if __name__ == '__main__':
    main()
    
    
