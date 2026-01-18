import requests
import json
import datetime
import re

BASE_URL = "https://www.dr.dk/drtv"
EPG_URL = "https://prod95-cdn.dr-massive.com/api/schedules"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'da,en-US;q=0.7,en;q=0.3'
}

CHANNEL_IDS = ['20875', '20876', '192099', '20892']

SENSOR_CONFIG = {
    "entity_id": "sensor.drtv_master_data",
    "friendly_name": "DRTV Master Data"
}

@time_trigger('cron(0 * * * *)')
def refresh_drtv_streams():
    """
    Scheduled trigger. 
    NOTE: If you want to update the input_select automatically on schedule,
    you must add the entity_id here in the call below.
    """
    log.info("Pyscript DRTV: Scheduled update started.")
    drtv_update_now()

@service
def drtv_update_now():
    """
    Manual update service.
    """
    try:
        # Execute the heavy lifting in a background thread
        data = task.executor(fetch_drtv_data, CHANNEL_IDS)
    except Exception as e:
        log.error(f"Pyscript DRTV: Thread execution failed: {e}")
        return

    if not data:
        log.warning("Pyscript DRTV: No data received from DR. Aborting update.")
        return

    # 1. Update Master Sensor
    state.set(
        SENSOR_CONFIG["entity_id"],
        datetime.datetime.now().isoformat(), 
        new_attributes={
            'friendly_name': SENSOR_CONFIG["friendly_name"],
            'icon': 'mdi:television-classic',
            'channels': data
        }
    )

    log.info("Pyscript DRTV: Update sequence completed.")

@pyscript_compile
def fetch_drtv_data(target_ids):
    """
    Fetches data from DR, extracts dynamic names, logos, streams and EPG.
    Returns a dictionary keyed by Channel Name.
    """
    # Output structure: { "DR1": { ... data ... }, "TVA Live": { ... } }
    output = {}
    
    # Mapping to link IDs (used in API) to Names (used in Output)
    # Populated dynamically during Phase 1
    id_to_name_map = {}

    session = requests.Session()
    session.headers.update(HEADERS)

    # Helper: Optimised Regex Resize
    def resize_image_url(url, width=320, height="square"):
        """
        Resizes DR image URLs.
        - Default (height="square"): Sets Width and Height to 'width' (Square crop/fill).
        - height=None: Removes Height param, letting the API decide (Keeps Aspect Ratio).
        - height=123: Sets a specific height.
        """
        if not url: return None
        try:
            # 1. Always set the width
            url = re.sub(r'Width=\d+', f'Width={width}', url)

            # 2. Handle height based on mode
            if height == "square":
                # Legacy behavior: Force square (ideal for logos)
                url = re.sub(r'Height=\d+', f'Height={width}', url)
            elif height is None:
                # NEW: Remove height entirely to preserve Aspect Ratio (ideal for posters)
                # The DR API automatically scales dimensions if one is missing.
                url = re.sub(r'&Height=\d+', '', url)
            else:
                # Set a specific height
                url = re.sub(r'Height=\d+', f'Height={height}', url)
                
            return url
        except Exception:
            return url

    try:
        # --- PHASE 1: SCRAPE (Find Names, Streams & Logos) ---
        r_front = session.get(f"{BASE_URL}/", timeout=10)

        if 'window.__data =' in r_front.text:
            raw = r_front.text.split('window.__data =')[1].split('</script>')[0].strip()
            if raw.endswith(';'): raw = raw[:-1]
            json_front = json.loads(raw)

            # A. Global Logo Lookup
            global_logos = json_front.get('app', {}).get('config', {}).get('linear', {}).get('channelsLogo', [])
            logo_map = {}
            for entry in global_logos:
                url = entry.get('url', '')
                for tid in target_ids:
                    if f"EntityId='{tid}'" in url or f"EntityId={tid}" in url:
                        logo_map[tid] = resize_image_url(url)

            # B. FIND LIVE LINK AND STREAMS
            nav_items = json_front.get('app', {}).get('config', {}).get('navigation', {}).get('header', [])
            live_path = next((item['path'] for item in nav_items if item.get('label') == 'LIVE'), None)

            if live_path:
                r_live = session.get(f"{BASE_URL}{live_path}", timeout=10)
                if 'window.__data =' in r_live.text:
                    raw_live = r_live.text.split('window.__data =')[1].split('</script>')[0].strip()
                    if raw_live.endswith(';'): raw_live = raw_live[:-1]
                    json_live = json.loads(raw_live)

                    cache_lists = json_live.get('cache', {}).get('list', {})
                    for key, val in cache_lists.items():
                        items = val.get('list', {}).get('items', [])
                        for item in items:
                            iid = str(item.get('id', ''))

                            if iid in target_ids:
                                channel_name = item.get('title', f"Channel {iid}")
                                id_to_name_map[iid] = channel_name

                                cf = item.get('customFields', {})
                                imgs = item.get('images', {})

                                # Resolve Logo
                                final_logo = logo_map.get(iid) or resize_image_url(imgs.get('logo'))

                                # Build Streams Object
                                streams = {
                                    'hls_primary': cf.get('hlsURL'),
                                    'hls_alt': cf.get('hlsAlternativeURL'),
                                    'hls_subtitles': cf.get('hlsWithSubtitlesURL'),
                                    'dash_primary': cf.get('dashURL')
                                }

                                # Init Output Object
                                output[channel_name] = {
                                    'id': iid,
                                    'title': 'Loading...',
                                    'description': 'Loading...',
                                    'logo': final_logo,
                                    'poster': imgs.get('wallpaper'),
                                    'streams': streams,
                                    'primary_stream': cf.get('hlsURL'),
                                    'start_time': None,
                                    'end_time': None,
                                    'debug': None
                                }

        # --- PHASE 2: API ---
        now = datetime.datetime.now()

        params = {
            'channels': ",".join(target_ids),
            'date': now.strftime('%Y-%m-%d'),
            'hour': now.hour,
            'duration': '24',
            'intersect': 'true',
            'device': 'web_browser',
            'lang': 'da',
            'ff': 'idp,ldp,rpt',
            'segments': 'drtv,optedin',
            'sub': 'Anonymous'
        }

        r_sched = session.get(EPG_URL, params=params, timeout=10)
        
        if r_sched.status_code == 200:
            sched_data = r_sched.json()

            for ch_data in sched_data:
                ch_id = str(ch_data.get('channelId'))

                # Use our map to find the correct dynamic name key
                if ch_id in id_to_name_map:
                    name_key = id_to_name_map[ch_id]

                    # Safety check if name exists in output
                    if name_key in output:
                        schedules = ch_data.get('schedules', [])

                        if schedules:
                            prog = schedules[0] # Current program
                            item = prog.get('item', {})
                            item_imgs = item.get('images', {})
                            
                            img_url = (
                                item_imgs.get('wallpaper') or 
                                item_imgs.get('tile') or 
                                item.get('primaryImage')
                            )

                            # Update existing object with EPG details
                            output[name_key].update({
                                'title': item.get('title'),
                                'description': item.get('shortDescription') or item.get('description'),
                                'poster': resize_image_url(img_url, 100, height=None),
                                'start_time': prog.get('startDate'),
                                'end_time': prog.get('endDate'),
                                'debug': params
                            })
        else:
            print(f"DRTV API Error: HTTP {r_sched.status_code}")

    except Exception as e:
        print(f"DRTV Critical Error: {str(e)}")
        return None

    return output
