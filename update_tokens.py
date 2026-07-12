import json
import requests
import re
import os

fav_path = os.path.join(os.path.dirname(__file__), "favorites.json")
ch_path = os.path.join(os.path.dirname(__file__), "channels.json")

# Define target mappings: stream path fragment -> channel name key
# We will match the stream ID in the M3U stream URL to identify the channel
channel_ids = {
    "2011670": "Sony Max HD",
    "2011671": "SET HD",
    "2011749": "SAB HD",
    "2011908": "MAX 2",
    "2011741": "Sony Pal",
    "2011746": "Sony Yay",
    "2011906": "Sony Wah"
}

def fetch_fresh_streams():
    url = "https://pzsl.pzcdn.workers.dev/?get-pl"
    headers = {"User-Agent": "mozila"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"Failed to fetch playlist: {r.status_code}")
            return None
        return r.text
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return None

def parse_m3u(m3u_content):
    streams = {}
    lines = m3u_content.splitlines()
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith("http"):
            # Look at previous line for info if needed, but we can match stream ID in the URL directly
            url = line
            for stream_id in channel_ids.keys():
                if f"/{stream_id}/" in url:
                    streams[stream_id] = url
    return streams

def update_json_files(fresh_streams):
    # 1. Update favorites.json
    with open(fav_path, "r", encoding="utf-8") as f:
        favorites = json.load(f)

    updated_favs = 0
    for fav in favorites:
        for stream_id, name in channel_ids.items():
            if fav["name"] == name:
                new_url = fresh_streams.get(stream_id)
                if new_url:
                    fav["stream"] = new_url
                    updated_favs += 1

    with open(fav_path, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=2, ensure_ascii=False)
    print(f"Updated {updated_favs} channels in favorites.json")

    # 2. Update channels.json
    with open(ch_path, "r", encoding="utf-8") as f:
        channels = json.load(f)

    updated_chs = 0
    for cat_name, ch_list in channels.items():
        for ch in ch_list:
            for stream_id, name in channel_ids.items():
                if ch["name"] == name:
                    new_url = fresh_streams.get(stream_id)
                    if new_url:
                        ch["stream"] = new_url
                        updated_chs += 1

    with open(ch_path, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)
    print(f"Updated {updated_chs} channels in channels.json")

def main():
    print("Fetching fresh streams...")
    m3u_content = fetch_fresh_streams()
    if not m3u_content:
        return
    
    print("Parsing M3U...")
    fresh_streams = parse_m3u(m3u_content)
    print(f"Found {len(fresh_streams)} matched channels in M3U:")
    for sid, url in fresh_streams.items():
        print(f"  - {channel_ids[sid]}: {url[:60]}...")

    if fresh_streams:
        update_json_files(fresh_streams)
        print("Update completed successfully!")
    else:
        print("No matching streams found in the M3U playlist.")

if __name__ == "__main__":
    main()
