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

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ Error fetching Steam workshop stats: {e}")
        return {}

    items = response.json().get('response', {}).get('publishedfiledetails', [])
    stats = {}

    for item in items:
        vote_data = item.get('vote_data', {})
        stats[item['title']] = {
            'downloads': item.get('lifetime_subscriptions', 0),
            'positive ratings': vote_data.get('votes_up', 0),
            'negative ratings': vote_data.get('votes_down', 0),
            'version': 'Unknown'
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
        "Better Shotgun Tooltip": 'https://thunderstore.io/c/lethal-company/p/AtomicStudio/Better_Shotgun_Tooltip',
        "Moved Magnet Switch": 'https://thunderstore.io/c/lethal-company/p/AtomicStudio/Moved_Magnet_Switch',
        "Atomics Cosmetics": 'https://thunderstore.io/c/lethal-company/p/AtomicStudio/Atomics_Cosmetics',
        "Colorable CozyLights": 'https://thunderstore.io/c/lethal-company/p/AtomicStudio/Colorable_CozyLights',
        "Atomics Suits": 'https://thunderstore.io/c/lethal-company/p/AtomicStudio/Atomics_Suits',
        "Breakable Windows": 'https://thunderstore.io/c/content-warning/p/AtomicStudio/Breakable_Windows',
        "Charging Divebell": 'https://thunderstore.io/c/content-warning/p/AtomicStudio/Charging_Divebell',
        "Toilet Paper Valuables": 'https://thunderstore.io/c/repo/p/AtomicStudio/Toilet_Paper_Valuables',
        "Speedy Escalators": 'https://thunderstore.io/c/peak/p/AtomicStudio/Speedy_Escalators',
        "Atomics Cosmetics PEAK": 'https://thunderstore.io/c/peak/p/AtomicStudio/Atomics_Cosmetics_PEAK',
        "Depleting Excess Extra Stamina": 'https://thunderstore.io/c/peak/p/AtomicStudio/Depleting_Excess_Extra_Stamina',
        "Green Screen": 'https://thunderstore.io/c/peak/p/AtomicStudio/Green_Screen'
    }

    total_downloads = 0
    total_ratings = 0
    total_ratings_bad = 0
    package_data = {}

    for name, url in packages.items():
        try:
            parts = url.strip('/').split('/')
            namespace = parts[-2]
            package_name = parts[-1]

            metrics_url = f'https://thunderstore.io/api/v1/package-metrics/{namespace}/{package_name}'
            version_url = f'https://thunderstore.io/api/v1/package/{namespace}/{package_name}'

            metrics_response = requests.get(metrics_url)
            metrics_response.raise_for_status()
            metrics_data = metrics_response.json()

            version_response = requests.get(version_url)
            version_response.raise_for_status()
            version_data = version_response.json()

            dls = metrics_data.get("downloads", 0)
            ratings = metrics_data.get("rating_score", 0)
            version = version_data.get("latest_version", "Unknown")

            total_downloads += dls
            total_ratings += ratings

            package_data[name] = {
                "downloads": dls,
                "ratings": ratings,
                "version": version
            }

        except requests.RequestException as e:
            print(f"⚠️ Error fetching {url}: {e}")

    steam_stats = get_workshop_stats(STEAM_WORKSHOP_IDS)
    steam_downloads = sum(stats.get('downloads', 0) for title, stats in steam_stats.items() if title != "last_checked")
    total_downloads += steam_downloads

    for title, stats in steam_stats.items():
        if title != "last_checked":
            total_ratings += stats.get('positive ratings', 0)
            total_ratings_bad += stats.get('negative ratings', 0)
            package_data[f"Steam - {title}"] = stats

    timestamp = steam_stats.get("last_checked", time.time())
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
    print(f"  - Likes:      {total_ratings:,}")
    print(f"  - Dislikes:   {total_ratings_bad:,}")
    print(f"  - Last Checked: {readable_time}")

    upload_to_gist(full_data)

if __name__ == "__main__":
    get_and_upload()
