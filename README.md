# NeerslagKompas 🌧️

Zelfstandige Home Assistant-integratie voor lokale neerslagvoorspellingen met Buienradar, Buienalarm en officiële KNMI-radar. Deze repository heet **HAweerkompas**; de integration domain is `neerslagkompas`.

**Status: 0.1.0-alpha.2. Experimenteel, vereist Home Assistant 2026.10.0 of hoger; nog niet live gevalideerd.** Niet gebruiken als enige bron voor veiligheidskritische automatiseringen.

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
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
python -m compileall -q custom_components/neerslagkompas
```

Zie [ARCHITECTURE.md](ARCHITECTURE.md) voor technische keuzes, tekortkomingen en verbeterstappen.

## Updates en releases via HACS

Gebruik een gepubliceerde versie, bijvoorbeeld `v0.1.0-alpha.2`, voor updates.
Schakel in HACS indien nodig de weergave van beta-/prereleases in om alpha-versies
te kunnen selecteren. Zonder releases kan de echte standaardbranch `main` worden
gebruikt. Selecteer geen korte commit-SHA als branch: `archive/refs/heads/c88ecef.zip`
verwijst naar een branch met die naam en levert 404 op als die niet bestaat.

Voor beheerders:

1. Verhoog `version` in `custom_components/neerslagkompas/manifest.json` via een PR.
2. Laat tests op Python 3.13 en 3.14 en hassfest slagen en merge de PR naar `main`.
3. Start **Actions → Publish NeerslagKompas release → Run workflow** op `main`.
   De workflow controleert dezelfde commit opnieuw en publiceert pas daarna een
   tag en GitHub Release met de manifestversie. Alpha/beta/rc blijven prereleases.
4. Bestaande versies worden niet overschreven; verhoog de versie voor de volgende
   release. HACS gebruikt het standaard GitHub-tagarchief; een eigen zipbestand
   of `zip_release`-instelling is niet nodig.

Bij een mislukte SHA-download: vernieuw de repository-informatie in HACS en kies
een gepubliceerde tag, of tijdelijk de branch `main`, via opnieuw downloaden.
Herstart daarna Home Assistant. Verwijder de NeerslagKompas-configuratie niet:
updaten behoudt bestaande config entries, API-sleutels, opties en entity IDs.
Deze release wijzigt geen unique IDs, sensornamen, providerinstellingen of data.

## Privacy en bronvermelding

Coördinaten gaan naar ingeschakelde bronservices; API-sleutels blijven in de eigen Home Assistant config entry en worden niet opgeslagen in GitHub, de diagnostiek of logs. Publicatievoorwaarden van Buienalarm/Infoplaza zijn **nog niet bevestigd**. De KNMI-open-data- en Buienradar-voorwaarden en verplichte bronvermelding moeten worden nageleefd.

Bronnen: KNMI Open Data, Buienradar.nl, Buienalarm/Infoplaza, Weerlive.nl.
