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

### Prerequisites
To use the dashboard card provided below, you need the following installed via **HACS**:
* [lovelace-layout-card](https://github.com/thomasloven/lovelace-layout-card)
* [auto-entities](https://github.com/thomasloven/lovelace-auto-entities)
* [card-mod](https://github.com/thomasloven/lovelace-card-mod)

### Step 1: Upload Frontend
1.  Download `tv_player.html` and `storebælt_tv.jpg` from this repository.
2.  Upload the files to your Home Assistant `www` folder:
    * `/config/www/tv_player.html`
    * `/config/www/images/icons/storebælt_tv.jpg`

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
```

### Step 4: Dashboard Card
Add the player to your Lovelace dashboard using a standard Webpage (Iframe) card.

```yaml
type: panel
path: tv
title: TV
icon: mdi:television
cards:
  - type: custom:layout-card
    layout_type: custom:grid-layout
    layout:
      grid-template-columns: 200px 1fr
      grid-template-rows: 1fr auto
      grid-gap: 0px
      margin: 0
      padding: 0
      grid-template-areas: |
        "sidebar video"
    cards:
      - type: custom:auto-entities
        view_layout:
          grid_area: sidebar
        card:
          type: grid
          columns: 1
          square: true
        card_param: cards
        filter:
          template: >-
            {% set sources = state_attr('sensor.tv_stream_context', 'sources') %}
            {% set options_entity = "input_select.tv_stream_source" %}

            {% set ns = namespace(cards = []) %}
            {% for option in state_attr(options_entity, 'options') %}
              {% if sources is not none and sources[option] is defined %}
                {% if is_state(options_entity, option) %}
                  {% set style = "ha-card { 
                      border: 3px solid white !important; 
                      box-shadow: 0 0 15px rgba(255, 255, 255, 0.4);
                      opacity: 1;
                      transform: scale(1.02); 
                      transition: all 0.3s ease-in-out;
                      z-index: 2;
                    }" %}
                {% else %}
                  {% set style = "ha-card { 
                      border: 3px solid transparent; 
                      opacity: 0.5; 
                      transform: scale(0.95); 
                      filter: grayscale(20%);
                      transition: all 0.3s ease-in-out;
                    }" %}
                {% endif %}
                {% set card = {
                  "type": "picture",
                  "image": sources[option].image,
                  "card_mod": {
                    "style": style
                  },
                  "tap_action": {
                    "action": "perform-action",
                    "perform_action": "input_select.select_option",
                    "target": {
                      "entity_id": options_entity
                    },
                    "data": {
                      "option": option
                    }
                  }
                } %}
                {% set ns.cards = ns.cards + [card] %}
              {% endif %}
            {% endfor %}

            {{ ns.cards }}

      - type: iframe
        url: /local/tv_player.html?entity=sensor.tv_stream_context
        aspect_ratio: 16:9
        hide_background: true
        view_layout:
          grid_area: video
    card_mod:
      style: |
        ha-card {
          height: 100vh !important;
          padding: 0 !important;
          margin: 0 !important;
          background: black;
        }

```
