# Architecture

## Goals

- Eén zelfstandige integration: geen afhankelijkheid van andere geïnstalleerde weerintegraties.
- KNMI, Buienradar en Buienalarm vanaf de eerste alpha, met toekomstige providers (zoals Rijkswaterstaat) als geïsoleerde adapters.
- Iedere provider houdt bron-, generatie- en vervaltijden, eenheden, geografische geldigheid en dataherkomst apart.
- Data quality first: een onbekende voorspelling wordt nooit impliciet droog.
- De backend berekent, Lovelace toont. Voorlopig nog geen eigen Lovelace-card.
- Meerdere locaties via config entries, unique ID onafhankelijk van coördinaten.

## Code

`providers/*.py`: afzonderlijke asynchrone HTTP-clients. `models.py`: immutable, timezone-aware `RainPoint` en `SourceData`. `coordinator.py`: onafhankelijk ophalen/foutstatus per bron. `engine.py`: eerste en eenvoudige bronovereenstemming voor nowcasts, geen gekalibreerd kansmodel. `sensor.py`, `binary_sensor.py`: Home Assistant entities. `config_flow.py`: UI-configuratie en lokale keys.

## KNMI radar

`radar_forecast/2.0` wordt via de KNMI Data Platform bestanden-API gedownload. De implementatie gebruikt HDF5, beeldgroepen en een polaire stereografische kaartprojectie. Cijfers in het raster staan in honderdsten mm per vijf minuten; voor mm/uur worden deze met 12 vermenigvuldigd. **De rastergeometrie, projectie (LU-pixeldefinitie), bestandsstructuur en kalibratie zijn getoetst aan een werkelijk KNMI-bestand van 9 oktober 2026.** De rastercel wordt met floor bepaald in plaats van nearest-corner afronding. Missing (65534) en outside-of-image (65535) worden uitgesloten en niet als droogte geïnterpreteerd. De h5py-wheel, netwerkbelasting en HAOS-end-to-end verwerking vragen nog praktijktests. Bij een onbekend format wordt geen resultaat gepubliceerd.

## Known risks before public release

- Ongepubliceerde Buienalarm-endpoint: legal/API-permission en rate limits.
- HDF5 `h5py` heeft native dependencies; HAOS platforms apart testen.
- KNMI volledige-rasterdownload is zwaar voor herhaalde requests door vele gebruikers; onderzoeken of ondersteunde point endpoint of event-based approach haalbaar is.
- KNMI Weerlive uur- en dagdata nog niet als eigen weather-entity.
- Tijdstempel rond zomertijd-/wintertijdwissels en gecachete voorspellingen verder testen.
- Geen lokale fysieke regenmeting.
- Eerste bronovereenstemming is heuristisch, zonder statistische betrouwbaarheidsscore.
- End-to-end integration tests met echte HA Core ontbreken.

## Roadmap

v0.1 alpha: providerclients, config flow, location, eigen sensors, tests en HACS-basis.

v0.1 beta: live KNMI-validatie en HACS/Hassfest green; HAOS-installatietest; beveiligde opties en config reload.

v0.2: weer- en uur/dagfuncties, historische validatie met waarnemingen.

v0.3: uitgebreidere buianalyse, bronprestatie en interpretatie.

v1.0: geteste publieke HACS-release.
