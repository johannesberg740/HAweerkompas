# NeerslagKompas 🌧️

Zelfstandige Home Assistant-integratie voor lokale neerslagvoorspellingen met Buienradar, Buienalarm en officiële KNMI-radar. Deze repository heet **HAweerkompas**; de integration domain is `neerslagkompas`.

**Status: 0.1.0-alpha.1. Experimenteel, nog niet live gevalideerd op Home Assistant OS 2026.10.1.** Niet gebruiken als enige bron voor veiligheidskritische automatiseringen.

## Via HACS installeren

1. Voeg in **HACS → ⋮ → Aangepaste repositories** toe: `https://github.com/johannesberg740/HAweerkompas`, type **Integration**.
2. Installeer **NeerslagKompas**. Herstart Home Assistant.
3. Voeg via **Instellingen → Apparaten en diensten → Integratie toevoegen** NeerslagKompas toe.
4. Kies een locatienaam en schakel *Thuislocatie volgen* in, of vul handmatige coördinaten in.
5. Schakel Buienradar/Buienalarm in en vul eventueel je **eigen** KNMI Data Platform- of Weerlive-API-sleutel in.
6. Controleer bronstatussen en sensoren. Bij ontbrekende gegevens moet `unavailable` verschijnen, niet "droog".

Bij een **private repository** kan HACS geen toegang hebben. In dat geval pas publiek maken na de controle van API-gebruiksvoorwaarden of voorlopig handmatig installeren. Er staan geen API-sleutels in de broncode.

## Providers

| Bron | Type | Beschikbaarheid |
|---|---|---|
| Buienradar.nl | Vijfminuten-neerslagverwachting | Zonder sleutel |
| Buienalarm / Infoplaza | Vijfminuten-neerslagverwachting | Experimentele endpoint; voorwaarden nog te controleren |
| KNMI Open Data `radar_forecast/2.0` | Officiële radarnowcast | Eigen API-sleutel vereist |
| KNMI via Weerlive.nl | Langere uur-/dagcontext | Eigen Weerlive-sleutel vereist |

KNMI-radar is vanaf deze alpha geïmplementeerd, maar **nog niet met echte KNMI-radarbestanden bevestigd**. De HDF5-parser en locatieprojectie gebruiken een synthetische testfixture; valideer op HAOS voor gebruik in productie.

## Functionaliteit alpha

- Eén centrale neerslagstatus gebaseerd op geldige vijfminutendata.
- Regen binnen 30 minuten, afzonderlijke providerstatussen en diagnostiek.
- Dynamische Home Assistant-thuislocatie, handmatige locatie en meerdere locaties.
- Elke provider heeft een eigen polling-coordinator. Bronuitval wordt afzonderlijk gemeld.
- Tijdstippen worden timezone-aware verwerkt. Intensiteit in mm/uur.
- Voorspellingen worden **nooit** als lokaal gemeten regen gepresenteerd.
- Weerlive wordt niet als vijfminutenradarstem meegeteld.

## Ontwikkeling

```shell
python -m pip install pytest h5py
python -m pytest -q tests
python -m compileall -q custom_components/neerslagkompas
```

Zie [ARCHITECTURE.md](ARCHITECTURE.md) voor technische keuzes, tekortkomingen en verbeterstappen.

## Privacy en bronvermelding

Coördinaten gaan naar ingeschakelde bronservices; API-sleutels blijven in de eigen Home Assistant config entry en worden niet opgeslagen in GitHub, de diagnostiek of logs. Publicatievoorwaarden van Buienalarm/Infoplaza zijn **nog niet bevestigd**. De KNMI-open-data- en Buienradar-voorwaarden en verplichte bronvermelding moeten worden nageleefd.

Bronnen: KNMI Open Data, Buienradar.nl, Buienalarm/Infoplaza, Weerlive.nl.
