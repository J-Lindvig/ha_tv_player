# HA TV Player 📺

A lightweight, robust, and fully synchronized HTML5 TV Player for **Home Assistant**.

This project implements a **"Smart Backend, Dumb Frontend"** architecture. All logic, stream URLs, and configuration reside in Home Assistant (YAML), while the HTML5 player is a generic renderer that syncs state via the Home Assistant API.

## 📑 Table of Contents
* [✨ Features](#-features)
* [🛠️ Architecture](#%EF%B8%8F-architecture)
* [🚀 Installation & Configuration](#-installation--configuration)
  * [Prerequisites](#prerequisites)
  * [Step 1: Upload Frontend](#step-1-upload-frontend)
  * [Step 2: Create Helpers](#step-2-create-helpers)
  * [Step 3: Create The Brain (Template Sensor)](#step-3-create-the-brain-template-sensor)
  * [Step 4: Dashboard Card](#step-4-dashboard-card)
  * [Step 5: Physical Remote Automation](#step-5-physical-remote-automation)

---

## ✨ Features

* **HLS Streaming:** Native support for `.m3u8` streams via `hls.js`.
* **Reactive PiP (Picture-in-Picture):** Automatically displays a security camera feed overlay when a binary sensor (e.g., motion/object detection) triggers.
* **Full Synchronization:** Volume and Mute are 2-way synced between the UI and HA entities. If you change the volume in HA, the player updates instantly.
* **Ghost Killer:** Automatically pauses the video stream when the dashboard card is not visible (using `IntersectionObserver`) to save bandwidth and CPU.
* **DRY & KISS:** No hardcoded entities in the HTML/JS. Everything is defined in a single Template Sensor.
* **Stateless Power Logic:** Uses `browser_mod` to detect the actual page state, ensuring the physical power button always works correctly (even after manual touch navigation).

---

## 🛠️ Architecture

1. **Helpers:** Store the state (Channel, Volume, Mute).
2. **Template Sensor (The Brain):** Maps channels to URLs, handles logic, and tells the player *which* entities to control.
3. **Frontend (The Face):** A generic `tv_player.html` file served via `iframe`.

---

## 🚀 Installation & Configuration

### Prerequisites
To use the dashboard card provided below, you need the following installed via **HACS**:
* [lovelace-layout-card](https://github.com/thomasloven/lovelace-layout-card)
* [auto-entities](https://github.com/thomasloven/lovelace-auto-entities)
* [card-mod](https://github.com/thomasloven/lovelace-card-mod)
* [browser_mod](https://github.com/thomasloven/hass-browser_mod) (Required for navigation and automation)

### Step 1: Upload Frontend
1. Download `tv_player.html` and `storebælt_tv.jpg` from this repository.
2. Upload the files to your Home Assistant `www` folder:
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
  tv_stream_pip_manual:
    name: TV PiP Manual
    icon: mdi:cctv

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
```

### Step 3: Create The Brain (Template Sensor)
This sensor is the heart of the system. It maps the selected source to a URL and exposes the configuration to the frontend.

Add this to your `configuration.yaml` (or `template.yaml`):

```yaml
# configuration.yaml

template:
  - triggers:
      - trigger: state
        entity_id:
          - input_select.tv_stream_source
          - input_number.tv_stream_volume
          - input_boolean.tv_stream_mute
          - binary_sensor.carport_object
          - input_boolean.tv_stream_pip_manual
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
            {% set base_url = "[https://prod95-static.dr-massive.com/api/shain/v1/dataservice/ResizeImage/$value?Format=%27png%27&Quality=90&Width=320&Height=320&ImageId=](https://prod95-static.dr-massive.com/api/shain/v1/dataservice/ResizeImage/$value?Format=%27png%27&Quality=90&Width=320&Height=320&ImageId=)" %}
            {% set map = {
              "DR 1": {
                "image": base_url ~ 2344192,
                "url": "[https://drlivedr1hls.akamaized.net/hls/live/2113625/drlivedr1/master.m3u8](https://drlivedr1hls.akamaized.net/hls/live/2113625/drlivedr1/master.m3u8)"
              },
              "DR 2": {
                "image": base_url ~ 46461911,
                "url": "[https://drlivedr2hls.akamaized.net/hls/live/2113623/drlivedr2/master.m3u8](https://drlivedr2hls.akamaized.net/hls/live/2113623/drlivedr2/master.m3u8)"
              },
              "TVA": {
                "image": base_url ~ 16100144,
                "url": "[https://drlivedrtvahls.akamaized.net/hls/live/2113613/drlivedrtva/master.m3u8](https://drlivedrtvahls.akamaized.net/hls/live/2113613/drlivedrtva/master.m3u8)"
              },
              "Ramasjang": {
                "image": base_url ~ 2399380,
                "url": "[https://drlivedrrhls.akamaized.net/hls/live/2113621/drlivedrr/master.m3u8](https://drlivedrrhls.akamaized.net/hls/live/2113621/drlivedrr/master.m3u8)"
              },
              "Storebælt": {
                "image": "/local/images/icons/storebælt_tv.jpg",
                "url": "[https://stream.sob.m-dn.net/live/sb1/index.m3u8](https://stream.sob.m-dn.net/live/sb1/index.m3u8)"
              }
            } %}
            {{ map }}
          stream_url: "{{ this.attributes.sources.get(states('input_select.tv_stream_source'), {'url': ''}).url }}"
          stream_image: "{{ this.attributes.sources.get(states('input_select.tv_stream_source'), {'image': ''}).image }}"
          stream_volume: "{{ states('input_number.tv_stream_volume') | float(0.5) }}"
          stream_mute: "{{ is_state('input_boolean.tv_stream_mute', 'on') }}"
          # PiP Logic: Active if motion sensor is ON OR Manual Override is ON
          pip_active: >-
            {{ is_state('binary_sensor.carport_object', 'on') 
               or is_state('input_boolean.tv_stream_pip_manual', 'on') }}
```

### Step 4: Dashboard Card
Add the player to your Lovelace dashboard. This configuration creates a sidebar with channel selection and the main video player.

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

### Step 5: Physical Remote Automation
This automation maps a physical Zigbee/MQTT remote (like IKEA Styrbar) to the TV logic. It interacts directly with the helpers and uses `browser_mod` for smart navigation and refresh functionality.

**Note:** Replace `DIN_DEVICE_ID` and `BROWSER_MOD ID` with your own IDs.

```yaml
automation:
  - alias: TV Kiosk Remote
    description: >-
      Controls TV power, volume, and channels via MQTT remote. 
      Includes "Panic Button" (Refresh) and stateless power logic.
    mode: single
    triggers:
      # --- POWER ---
      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: brightness_move_up
        trigger: device
        id: power_toggle
        alias: "☀ Long Press (Power)"

      # --- MUTE ---
      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: brightness_move_down
        trigger: device
        id: mute
        alias: "☼ Long Press (Mute)"

      # --- VOLUME ---
      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: "on"
        trigger: device
        id: volume_up
        alias: "☀ Short Press (Vol Up)"
      
      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: "off"
        trigger: device
        id: volume_down
        alias: "☼ Short Press (Vol Down)"

      # --- REFRESH ---
      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: arrow_right_hold
        trigger: device
        id: refresh
        alias: "> Long Press (Refresh)"

      # --- PIP ---
      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: arrow_left_hold
        trigger: device
        id: pip
        alias: "< Long Press (PiP)"

      # --- CHANNELS ---
      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: arrow_right_click
        trigger: device
        id: channel_up
        alias: "> Short Press (Next)"

      - domain: mqtt
        device_id: DIN_DEVICE_ID  # <--- REPLACE WITH REMOTE DEVICE ID
        type: action
        subtype: arrow_left_click
        trigger: device
        id: channel_down
        alias: "< Short Press (Prev)"

    conditions: []
    actions:
      - choose:
          # 1. POWER (Stateless Logic)
          - conditions:
              - condition: trigger
                id: power_toggle
            sequence:
              - if:
                  - condition: template
                    value_template: >-
                      {# Checks Browser Mod sensor: Does URL end with '0'? #}
                      {# REMEMBER: Change 'sensor.kiosk_browser_path' to your tablet sensor #}
                      {{ (state_attr('sensor.kiosk_browser_path', 'pathSegments') or []) | last == '0' }}
                    alias: Is TV Off (Page 0)?
                then:
                  - action: browser_mod.navigate
                    data:
                      browser_id:
                        - ec7c4a68ca59c058e65cf6313de20c06  # <--- REPLACE WITH YOUR BROWSER_MOD ID
                      path: /lovelace/tv                    # <--- PATH TO TV PAGE
                    alias: Turn ON TV
                else:
                  - action: browser_mod.navigate
                    data:
                      browser_id:
                        - ec7c4a68ca59c058e65cf6313de20c06  # <--- REPLACE WITH YOUR BROWSER_MOD ID
                      path: /lovelace/0                     # <--- PATH TO OFF PAGE
                    alias: Turn OFF TV
            alias: Power Toggle

          # 2. MUTE
          - conditions:
              - condition: trigger
                id: mute
            sequence:
              - action: input_boolean.toggle
                target:
                  entity_id: input_boolean.tv_stream_mute
            alias: Mute

          # 3. VOLUME
          - conditions:
              - condition: trigger
                id:
                  - volume_up
                  - volume_down
            sequence:
              - action: input_number.set_value
                target:
                  entity_id: input_number.tv_stream_volume
                data:
                  value: >-
                    {% set current = states('input_number.tv_stream_volume') | float(0) %}
                    {% set step = 0.05 %}
                    {% if trigger.id == 'volume_up' %}
                      {{ [current + step, 1.0] | min }}
                    {% else %}
                      {{ [current - step, 0.0] | max }}
                    {% endif %}
              - if:
                  - condition: trigger
                    id: volume_up
                  - condition: state
                    entity_id: input_boolean.tv_stream_mute
                    state: "on"
                then:
                  - action: input_boolean.turn_off
                    target:
                      entity_id: input_boolean.tv_stream_mute
            alias: Volume up/down

          # 4. CHANNELS
          - conditions:
              - condition: trigger
                id: channel_up
            sequence:
              - action: input_select.select_next
                target:
                  entity_id: input_select.tv_stream_source
                data:
                  cycle: true
            alias: Channel up

          - conditions:
              - condition: trigger
                id: channel_down
            sequence:
              - action: input_select.select_previous
                target:
                  entity_id: input_select.tv_stream_source
                data:
                  cycle: true
            alias: Channel down

          # 5. REFRESH
          - conditions:
              - condition: trigger
                id: refresh
            sequence:
              - action: browser_mod.refresh
                data:
                  browser_id:
                    - ec7c4a68ca59c058e65cf6313de20c06  # <--- REPLACE WITH YOUR BROWSER_MOD ID
            alias: Refresh

          # 6. PIP
          - conditions:
              - condition: trigger
                id: pip
            sequence:
              - action: input_boolean.toggle
                target:
                  entity_id: input_boolean.tv_stream_pip_manual
            alias: PiP
```
