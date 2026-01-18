# HA TV Player 📺 (v3.1)

A lightweight, robust, and fully synchronized HTML5 TV Player for **Home Assistant**.

This project implements a **"Smart Backend, Dumb Frontend"** architecture. All logic, stream URLs, and configuration reside in Home Assistant (YAML), while the HTML5 player is a generic renderer that syncs state via the Home Assistant API.

### ⚠️ Important: EPG & Dynamic Streams
This player uses a **Hybrid Architecture**:
1.  **With Pyscript (Recommended):** Fetches **Live EPG** (Program titles, descriptions, posters) and dynamic stream URLs directly from DR via a backend script.
2.  **Without Pyscript (Fallback):** The player still works perfectly with a built-in static channel list, but **without** EPG metadata (program info).

## 📑 Table of Contents
* [✨ Features](#-features)
* [🛠️ Architecture](#%EF%B8%8F-architecture)
* [🚀 Installation & Configuration](#-installation--configuration)

---

## ✨ Features

* **Live EPG:** Real-time program titles, descriptions, and poster art (requires Pyscript).
* **HLS Streaming:** Native support for `.m3u8` streams via `hls.js`.
* **Reactive PiP:** Automatically displays a security camera feed overlay when a binary sensor (e.g., motion/object detection) triggers.
* **Full Synchronization:** Volume and Mute are 2-way synced between the UI and HA entities.
* **Ghost Killer:** Automatically pauses the video stream when the dashboard card is not visible to save bandwidth and CPU.
* **Hybrid Source Aggregation:** Automatically merges dynamic streams (DRTV), static fallbacks, and custom user channels (e.g. webcams).

---

## 🛠️ Architecture

1.  **Backend Scraper (Pyscript):** Periodically fetches JSON data from DRTV (EPG & Stream URLs).
2.  **Template Sensor (The Brain):** Merges data sources. If the scraper is down, it reverts to a hardcoded "Safety Net" list.
3.  **Frontend (The Face):** A generic `tv_player.html` file that renders whatever the Template Sensor tells it to.

---

## 🚀 Installation & Configuration

### Prerequisites
To use this setup, you need the following installed via **HACS**:
* `lovelace-layout-card`
* `auto-entities`
* `card-mod`
* `browser_mod`
* `pyscript` (Recommended for EPG)

### Step 1: Install Pyscript (Recommended)
*Fetches live EPG data and dynamic streams.*

1.  Ensure Pyscript is installed and loaded.
2.  Download [drtv_streams.py](/config/pyscript/drtv_streams.py).
3.  Place the file in your HA config folder: `/config/pyscript/drtv_streams.py`.
4.  Reload Pyscript.

### Step 2: Upload Frontend
1.  Download [tv_player.html](/config/www/tv_player.html).
2.  Download [storebaelt_tv.jpg](/config/www/images/icons/storebaelt_tv.jpg).
3.  Upload them to `/config/www/` (and `/config/www/images/icons/` respectively).

### Step 3: Backend Configuration (The Brain)
We have consolidated all Helpers, Template Sensors, and Automations into a single file for easy setup.

1.  Download [configuration.yaml](/config/configuration.yaml).
2.  Open the file and copy the contents directly into your `configuration.yaml`.
3.  *Alternative:* You can create the Helpers (`input_boolean`, `input_number`, etc.) manually via the GUI (**Settings > Devices & Services > Helpers**), but the `template` sensor logic **must** be added to your YAML configuration.

### Step 4: Dashboard Card
1.  Download the dashboard YAML code: [lovelace.yaml](/config/lovelace.yaml).
2.  Create a new View in your dashboard (Panel Mode recommended).
3.  Paste the YAML code into a card.

### Step 5: Remote Control (Optional)
If you want to control the TV with a physical Zigbee remote (like IKEA Styrbar), use this automation blueprint.

1.  Download [automations.yaml](/config/automations.yaml).
2.  Adjust the `device_id` to match your specific remote.
