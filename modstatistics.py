import requests
import os
import json
import time
from datetime import datetime

GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

STEAM_WORKSHOP_IDS = [
    "3383270520",
    "3383837077",
    "3385201967",
    "3385250537",
    "3386220143",
    "3386777900",
    "3389296239",
    "3400376437"
]

def get_workshop_stats(ids):
    url = "https://api.steampowered.com/IPublishedFileService/GetDetails/v1/"
    params = {
        'key': STEAM_API_KEY,
        'includevotes': 'true'
    }

    for i, wid in enumerate(ids):
        params[f'publishedfileids[{i}]'] = wid

    response = requests.get(url, params=params)
    response.raise_for_status()

    items = response.json()['response']['publishedfiledetails']
    stats = {}

    for item in items:
        vote_data = item.get('vote_data', {})
        stats[item['title']] = {
            'downloads': item.get('lifetime_subscriptions', 0),
            'positive ratings': vote_data.get('votes_up', 0),
            'negative ratings': vote_data.get('votes_down', 0)
        }

    stats["last_checked"] = time.time()
    return stats

def upload_to_gist(data):
    gist_data = {
        "files": {
            "prev.json": {
                "content": json.dumps(data, indent=4)
            }
        }
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.patch(f"https://api.github.com/gists/{GIST_ID}", json=gist_data, headers=headers)

    if response.status_code == 200:
        print("✅ Successfully uploaded data to Gist!")
    else:
        print(f"❌ Failed to upload data to Gist: {response.status_code} - {response.text}")

def get_and_upload():
    packages = {
        "Better Shotgun Tooltip": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Better_Shotgun_Tooltip/',
        "Moved Magnet Switch": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Moved_Magnet_Switch/',
        "Atomics Cosmetics": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Atomics_Cosmetics/',
        "Colorable CozyLights": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Colorable_CozyLights/',
        "Atomics Suits": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Atomics_Suits/',
        "Breakable Windows": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Breakable_Windows/',
        "Charging Divebell": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Charging_Divebell/',
        "Toilet Paper Valuables": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Toilet_Paper_Valuables/',
        "Speedy Escalators": 'https://thunderstore.io/api/v1/package-metrics/AtomicStudio/Speedy_Escalators/'
    }

    total_downloads = 0
    total_ratings = 0
    total_ratings_bad = 0
    package_data = {}

    for name, url in packages.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            dls = data["downloads"]
            ratings = data["rating_score"]

            total_downloads += dls
            total_ratings += ratings

            package_data[name] = {
                "downloads": dls,
                "ratings": ratings
            }

        except requests.RequestException as e:
            print(f"⚠️ Error fetching {url}: {e}")

    steam_stats = get_workshop_stats(STEAM_WORKSHOP_IDS)
    steam_downloads = sum(stats['downloads'] for title, stats in steam_stats.items() if title != "last_checked")
    total_downloads += steam_downloads

    for title, stats in steam_stats.items():
        if title != "last_checked":
            total_ratings += stats['positive ratings']
            total_ratings_bad += stats['negative ratings']
            package_data[f"Steam - {title}"] = stats

    timestamp = steam_stats["last_checked"]
    readable_time = datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M:%S')

    full_data = {
        "total_downloads": total_downloads,
        "total_ratings": total_ratings,
        "total_ratings_bad": total_ratings_bad,
        "last_checked": timestamp,
        **package_data
    }

    print(f"\n✅ Totals:")
    print(f"  - Downloads: {total_downloads:,}")
    print(f"  - Likes:     {total_ratings:,}")
    print(f"  - Dislikes:  {total_ratings_bad:,}")
    print(f"  - Last Checked: {readable_time}")

    upload_to_gist(full_data)

if __name__ == "__main__":
    get_and_upload()
