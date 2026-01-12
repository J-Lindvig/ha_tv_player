# HA TV Player 📺

A lightweight, robust, and fully synchronized HTML5 TV Player for **Home Assistant**.

This project implements a **"Smart Backend, Dumb Frontend"** architecture. All logic, stream URLs, and configuration reside in Home Assistant (YAML), while the HTML5 player is a generic renderer that syncs state via the Home Assistant API.

## ✨ Features

* **HLS Streaming:** Native support for `.m3u8` streams via `hls.js`.
* **Reactive PiP (Picture-in-Picture):** Automatically displays a security camera feed overlay when a binary sensor (e.g., motion/object detection) triggers.
* **Full Synchronization:** Volume and Mute are 2-way synced between the UI and HA entities. If you change the volume in HA, the player updates instantly.
* **Ghost Killer:** Automatically pauses the video stream when the dashboard card is not visible (using `IntersectionObserver`) to save bandwidth and CPU.
* **DRY & KISS:** No hardcoded entities in the HTML/JS. Everything is defined in a single Template Sensor.
* **Dynamic Tokens:** Fetches camera access tokens on-demand to prevent stale authentication issues.

---

## 🛠️ Architecture

1.  **Helpers:** Store the state (Channel, Volume, Mute).
2.  **Template Sensor (The Brain):** Maps channels to URLs, handles logic, and tells the player *which* entities to control.
3.  **Frontend (The Face):** A generic `tv_player.html` file served via `iframe`.

---

## 🚀 Installation & Configuration

### Step 1: Upload Frontend
1.  Download `tv_player.html` from this repository.
2.  Upload the file to your Home Assistant `www` folder:
    * Path: `/config/www/tv_player.html`

### Step 2: Create Helpers
Add the following helpers to your `configuration.yaml` (or create them via **Settings > Devices & Services > Helpers**).

These entities store the state of the player.

```yaml
# configuration.yaml

input_boolean:
  tv_stream_mute:
    name: TV Stream Mute
    icon: mdi:volume-mute

input_number:
  tv_stream_volume:
    name: TV Stream Volume
    min: 0
    max: 1
    step: 0.01
    mode: slider
    icon: mdi:volume-high

input_select:
  tv_stream_source:
    name: TV Stream Source
    options:
      - DR 1
      - DR 2
      - TVA
      - Ramasjang
      - Storebælt
    icon: mdi:television

template:
  - triggers:
      - trigger: state
        entity_id:
          - input_select.tv_stream_source
          - input_number.tv_stream_volume
          - input_boolean.tv_stream_mute
          - binary_sensor.carport_object
      - trigger: homeassistant
        event: start
      - trigger: event
        event_type: event_template_reloaded
    sensor:
      - name: "TV Stream Context"
        unique_id: cfacca7667c34ffca4310d9d46c1334d
        state: "{{ states('input_select.tv_stream_source') }}"
        attributes:
          config_entity_volume: "input_number.tv_stream_volume"
          config_entity_mute: "input_boolean.tv_stream_mute"
          config_entity_camera: "camera.carport_fluent_lens_1"
          sources: >
            {% set base_url = "https://prod95-static.dr-massive.com/api/shain/v1/dataservice/ResizeImage/$value?Format=%27png%27&Quality=90&Width=320&Height=320&ImageId=" %}
            {% set map = {
              "DR 1": {
                "image": base_url ~ 2344192,
                "url": "https://drlivedr1hls.akamaized.net/hls/live/2113625/drlivedr1/master.m3u8"
              },
              "DR 2": {
                "image": base_url ~ 46461911,
                "url": "https://drlivedr2hls.akamaized.net/hls/live/2113623/drlivedr2/master.m3u8"
              },
              "TVA": {
                "image": base_url ~ 16100144,
                "url": "https://drlivedrtvahls.akamaized.net/hls/live/2113613/drlivedrtva/master.m3u8"
              },
              "Ramasjang": {
                "image": base_url ~ 2399380,
                "url": "https://drlivedrrhls.akamaized.net/hls/live/2113621/drlivedrr/master.m3u8"
              },
              "Storebælt": {
                "image": "/local/images/icons/storebælt_tv.jpg",
                "url": "https://stream.sob.m-dn.net/live/sb1/index.m3u8"
              }
            } %}
            {{ map }}
          stream_url: "{{ this.attributes.sources.get(states('input_select.tv_stream_source'), {'url': ''}).url }}"
          stream_volume: "{{ states('input_number.tv_stream_volume') | float(0.5) }}"
          stream_mute: "{{ is_state('input_boolean.tv_stream_mute', 'on') }}"
          pip_active: "{{ is_state('binary_sensor.carport_object', 'on') }}"
