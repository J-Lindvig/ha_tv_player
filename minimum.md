## ⚡ Quick Start (Minimal Install), - Volume, - Mute, - PiP

Få liv i systemet på 3 minutter med kun 3 trin.

* [1. Filer](#1-filer)
* [2. Backend (configuration.yaml)](#2-backend-configurationyaml)
* [3. Simple UI (Standard Cards)](#3-simple-ui-standard-cards)

### 1. Filer
Læg [tv_player.html](config/www/tv_player.html) i din `/config/www/` mappe.

### 2. Backend (configuration.yaml)
Indsæt dette i din `configuration.yaml` for at oprette en Kanalvælger og "Hjernen" (Sensoren der kobler det hele sammen).

```yaml
# 1. HELPERS
input_select:
  tv_stream_source:
    name: TV Kanal
    options: ["DR 1", "DR 2", "TVA", "Ramasjang"]
    icon: mdi:television

# 2. LOGIK (THE BRAIN)
template:
  - triggers:
      - trigger: state
        entity_id:
          - input_select.tv_stream_source
      - trigger: homeassistant
        event: start
      - trigger: event
        event_type: event_template_reloaded
    sensor:
      - name: "TV Stream Context"
        unique_id: cfacca7667c34ffca4310d9d46c1334d
        state: "{{ states('input_select.tv_stream_source') }}"
        attributes:
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
              }
            } %}
            {{ map }}
          stream_url: "{{ this.attributes.sources.get(states('input_select.tv_stream_source'), {'url': ''}).url }}"
          stream_image: "{{ this.attributes.sources.get(states('input_select.tv_stream_source'), {'image': ''}).image }}"
```
  ### 3. Simple UI (Standard Cards)
Hvis du vil teste setup'et uden at installere custom cards (som layout-card eller auto-entities), kan du bruge denne konfiguration. Den viser afspilleren øverst og en simpel betjeningsmenu nederst.

```yaml
type: vertical-stack
title: TV Kiosk (Simple)
cards:
  # 1. SELVE TV AFSPILLEREN
  - type: iframe
    url: /local/tv_player.html?entity=sensor.tv_stream_context
    aspect_ratio: 16:9
    title: Afspiller

  # 2. BETJENING (Helpers)
  - type: entities
    title: Betjening
    show_header_toggle: false
    entities:
      - entity: input_select.tv_stream_source
        name: Kanalvælger
```
