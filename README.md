# HA TV Player 📺

A lightweight, robust, and fully synchronized HTML5 TV Player for **Home Assistant**.

This project implements a "Smart Backend, Dumb Frontend" architecture. All logic, stream URLs, and configuration reside in Home Assistant (YAML), while the HTML5 player is a generic renderer that syncs state via the HA API.

## ✨ Features

* **HLS Streaming:** Native support for `.m3u8` streams via `hls.js`.
* **Reactive PiP (Picture-in-Picture):** Automatically pops up a security camera feed when a binary sensor (e.g., motion/object detection) triggers.
* **Full Synchronization:** Volume and Mute are 2-way synced between the UI and HA entities.
* **Ghost Killer:** Automatically pauses the video stream when the dashboard card is not visible (using `IntersectionObserver`) to save bandwidth and performance.
* **DRY & KISS:** No hardcoded entities in the HTML/JS. Everything is defined in a single Template Sensor.
* **Dynamic Tokens:** Fetches camera access tokens on-demand to prevent stale authentication.

---

## 🛠️ Architecture

1.  **Helpers:** Store the state (Channel, Volume, Mute).
2.  **Template Sensor (The Brain):** Maps channels to URLs, handles logic, and tells the player which entities to control.
3.  **Frontend (The Face):** A generic `tv_player.html` file served via `iframe`.

---

## 🚀 Installation

### 1. Create Helpers
Add the following helpers to your `configuration.yaml` (or via GUI). These store the state of the player.

```yaml
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
