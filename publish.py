import requests, json, os

from PIL import Image
from datetime import datetime

if not os.path.exists("icons"):
    os.makedirs("icons")

print("Loading repo list")

with open("repos.json", "r") as f:
   plugins = json.load(f)

print("Loading official repo")

official_repo = requests.get("https://kamori.goats.dev/Plugin/PluginMaster").json()

def get_asset_by_name(assets, name):
    for asset in assets:
        if asset['name'] == name:
            return asset
    return None

def get_asset_by_type(assets, mime_type):
    for asset in assets:
        if asset['content_type'] == mime_type:
            return asset
    return None

def get_github_download_count(username, repo):
    releases = requests.get(f"https://api.github.com/repos/{username}/{repo}/releases?per_page=100").json()
    download_count = 0
    for release in releases:
        asset = get_asset_by_name(release['assets'], "latest.zip")
        if asset:
            download_count += asset['download_count']
        asset = get_asset_by_name(release['assets'], "latestUnofficial.zip")
        if asset:
            download_count += asset['download_count']
    return download_count

def get_official_download_count(internal_name):
    for plugin in official_repo:
        if plugin['InternalName'] == internal_name:
            return plugin['DownloadCount']
    return 0

#unofficial_icon = Image.open("unofficial.png").convert("RGBA")
def create_icon(icon_url, internal_name, is_unofficial):
    with Image.open(requests.get(icon_url, stream=True).raw) as base_icon:
        icon = base_icon.convert("RGBA").resize((128, 128), Image.Resampling.LANCZOS)
        #if is_unofficial:
        #    icon.alpha_composite(unofficial_icon)
        icon.save(f"icons/{internal_name}.png")
    return icon_url

plogons = []
good_plogons = []

for plugin in plugins:
    print(f"Loading repo {plugin['username']}/{plugin['repo']}")

    release_info = requests.get(f"https://api.github.com/repos/{plugin['username']}/{plugin['repo']}/releases/latest").json()

    print(f"Loading release data")

    release_timestamp = int(datetime.fromisoformat(release_info['published_at'].replace('Z','+00:00')).timestamp())
    zip_asset = get_asset_by_name(release_info['assets'], "latest.zip")
    config_asset = get_asset_by_type(release_info['assets'], "application/json")

    if zip_asset is None or config_asset is None:
        raise Exception("No release zip or config found")

    print(f"Loading manifest")

    zip_download_url = zip_asset['browser_download_url']
    config_data = requests.get(config_asset['browser_download_url']).json()

    print(f"Loading download counts")

    download_count = get_github_download_count(plugin['username'], plugin['repo'])
    if plugin["official"]:
        download_count += get_official_download_count(config_data['InternalName'])

    config_data['IsHide'] = False
    config_data['IsTestingExclusive'] = False
    config_data['LastUpdate'] = release_timestamp
    config_data['DownloadCount'] = download_count
    config_data['DownloadLinkInstall'] = zip_download_url
    config_data['DownloadLinkUpdate'] = zip_download_url
    config_data['DownloadLinkTesting'] = zip_download_url
    icon_url = config_data['IconUrl']
    config_data['IconUrl'] = create_icon(icon_url, config_data['InternalName'], False)

    plogons.append(config_data.copy())

    unofficial_zip_asset = get_asset_by_name(release_info['assets'], "latestUnofficial.zip")
    if unofficial_zip_asset is not None:
        zip_download_url = unofficial_zip_asset['browser_download_url']

        config_data['Punchline'] = f"Unofficial/uncertified build of {config_data['Name']}. {config_data['Punchline']}"
        config_data['Name'] += ' (Unofficial)'
        config_data['InternalName'] += 'Unofficial'
        config_data['IconUrl'] = create_icon(icon_url, config_data['InternalName'], True)
        config_data['DownloadLinkInstall'] = zip_download_url
        config_data['DownloadLinkUpdate'] = zip_download_url
        config_data['DownloadLinkTesting'] = zip_download_url
        good_plogons.append(config_data.copy())

print("Writing repo jsons")

with open('plogon.json', 'w') as f:
    json.dump(plogons, f, indent=4)

with open('goodplogon.json', 'w') as f:
    json.dump(good_plogons, f, indent=4)