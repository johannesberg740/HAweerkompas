# NeerslagKompas: voorspelling als grafiek

Deze Lovelace-kaart gebruikt **ApexCharts Card** via HACS (custom:apexcharts-card).
De backend levert vijfminutenvoorspellingen in mm/uur. De grafiek bevat geen
berekeningen of alternatieve provider-aanvragen. Het interval is voor sommige
bronnen vijf minuten, maar ontbrekende waarden worden niet als nul weergegeven.

Voeg een **Handmatige kaart** toe met de onderstaande YAML. De entity IDs horen
bij de eerste NeerslagKompas-installatie met locatie **Thuis**; bij een
andere locatie of hernoemde entity-ID moet je deze drie waarden aanpassen.

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: NeerslagKompas · Komende 2 uur
  show_states: false
graph_span: 2h
span:
  start: minute
now:
  show: true
  label: Nu
apex_config:
  chart:
    height: 280
  stroke:
    curve: straight
    width: 2
  tooltip:
    shared: true
yaxis:
  - id: intensity
    min: 0
    decimals: 1
    apex_config:
      title:
        text: mm/uur
series:
  - entity: sensor.neerslagkompas_thuis_bron_knmi_radar
    name: KNMI
    type: line
    color: "#2196F3"
    yaxis_id: intensity
    extend_to: false
    data_generator: |
      return (entity.attributes.forecast_points || [])
        .map(p => [new Date(p.datetime).getTime(), p.intensity_mm_h]);
  - entity: sensor.neerslagkompas_thuis_bron_buienradar
    name: Buienradar
    type: line
    color: "#22A06B"
    yaxis_id: intensity
    extend_to: false
    data_generator: |
      return (entity.attributes.forecast_points || [])
        .map(p => [new Date(p.datetime).getTime(), p.intensity_mm_h]);
  - entity: sensor.neerslagkompas_thuis_bron_buienalarm
    name: Buienalarm
    type: line
    color: "#F59E0B"
    yaxis_id: intensity
    extend_to: false
    data_generator: |
      return (entity.attributes.forecast_points || [])
        .map(p => [new Date(p.datetime).getTime(), p.intensity_mm_h]);
```

## Hoe lees je de grafiek?

- De drie lijnen zijn onafhankelijke **bronvoorspellingen**, niet gemeten neerslag.
- De y-as toont de **neerslagintensiteit** in mm/uur.
- Lege lijnen betekenen: provider niet geconfigureerd, geen verse voorspelling
  of geen punten in het tijdvenster. Dat betekent **niet** 'geen regen'.
- De grafiek toont expliciet alleen punten in de komende twee uur. Data in de
  afgelopen vijf minuten wordt door de kaart buiten het zichtbare venster gelaten.
- Een bron kan kortere dekking hebben dan twee uur; we vullen de rest niet aan.
- De KNMI-radar haalt de voorspelling uit de circa 1 km rastercel van de
  ingestelde locatie. Dat is de **ruimtelijke rasterresolutie**, geen garantie
  voor nauwkeurigheid op één kilometer.
- Voor elke bron kun je in **Ontwikkelaarstools → Statussen** de attributen
  `forecast_points`, `last_received`, `latitude`, `longitude`,
  `forecast_start`, `forecast_end` en (KNMI) `spatial_resolution_km`
  controleren.

## Compatibiliteit

De bestaande entity-ID's, API-sleutels, frequenties en consensusberekening
blijven behouden. ApexCharts wordt **niet** als integratiedependency vereist;
zonder kaart blijven de sensorattributen toegankelijk. De volledige weergave
moet nog in Home Assistant visueel worden getest.

###########################################################
# Purpose
# Toont actuele regenverwachtingen van KNMI, Buienradar en Buienalarm.
#
# Why
# Geeft zicht op verschillen tussen bronnen bij dezelfde thuislocatie.
#
# Changes
# 2026-10-09 - ApexCharts-voorbeeld met drie voorspelde tijdreeksen.
#
# Old entity names
# Geen: bestaande bronsensoren en unique IDs blijven ongewijzigd.
###########################################################
