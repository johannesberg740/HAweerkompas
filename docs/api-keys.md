# API-sleutels instellen voor NeerslagKompas

NeerslagKompas kan zonder API-sleutels werken met Buienradar en Buienalarm. **KNMI Open Data en Weerlive zijn optioneel en standaard niet geactiveerd** totdat je zelf een bijpassende sleutel invult. De repository bevat geen echte API-sleutels.

## 1. Officiële KNMI-radar: KNMI Data Platform

Je hebt de **geregistreerde Open Data API-key** nodig, niet een sleutel voor Weerlive, EDR, WMS of Notification Service.

1. Lees de officiële [KNMI Open Data API-handleiding](https://developer.dataplatform.knmi.nl/open-data-api).
2. Voor registratie: raadpleeg de [actuele mededelingen van het KNMI](https://developer.dataplatform.knmi.nl/news). **Sinds juni 2026 is zelfstandig registreren via het portaal tijdelijk niet mogelijk; mail voor een account naar `opendata@knmi.nl`.**
3. Na het verkrijgen van toegang: open de [KNMI API Catalogue](https://developer.dataplatform.knmi.nl/apis/), kies **Open Data API** en **Request an API key**. Noteer de volledige sleutel op het moment dat die wordt getoond.
4. Open Home Assistant: **Instellingen → Apparaten en diensten → NeerslagKompas → Configureren**.
5. Vul je sleutel in bij **KNMI Data Platform API-sleutel (optioneel)** en sla op.
6. Controleer de bronstatus van **KNMI-radar**. Als de bron niet beschikbaar is, raadpleeg de logboeken.

De Open Data API verwacht de *volledige sleutel* in de HTTP-header `Authorization`. NeerslagKompas stelt die header zelf in. Je hoeft geen `Bearer`-voorvoegsel in te typen.

**Status van de radar in de huidige alpha:** de `radar_forecast/2.0`-module is experimenteel. HDF5-uitlezing en locatieprojectie zijn nog niet met werkelijke KNMI-radarbestanden geverifieerd. Een correcte API-sleutel garandeert dus nog geen werkende radar. Bij een bronfout tonen we niet beschikbaar in plaats van een onterechte melding 'droog'.

## 2. Weerlive: KNMI-weerinformatie en verwachtingen

Weerlive gebruikt een **eigen API-key**, die niet uitwisselbaar is met de KNMI Data Platform-sleutel.

1. Ga naar [Weerlive: KNMI Weer API](https://weerlive.nl/delen.php).
2. Vraag via de sectie **API Key** een gratis eigen API-key aan.
3. Open **Instellingen → Apparaten en diensten → NeerslagKompas → Configureren**.
4. Vul de sleutel in bij **Weerlive API-sleutel (optioneel)**.
5. Sla op en controleer de bronstatus van **Weerlive**.

Weerlive publiceert een grens van **300 aanvragen per dag** voor de gratis API en gebruiksvoorwaarden voor studie- en privédoeleinden met bronvermelding. De gegevens zijn uur- en dagverwachtingen, geen officiële vijfminuten-radarnowcast.

## 3. Veilig configureren en beheren

- **Geen sleutel:** de bijbehorende KNMI Data Platform- of Weerlive-bron wordt niet gestart. Buienradar en Buienalarm hebben geen persoonlijke sleutel nodig.
- **Wel een sleutel:** de sleutel staat in de lokale Home Assistant-configuratie van die NeerslagKompas-installatie, niet op GitHub.
- **Sleutel wijzigen:** gebruik **Configureren** en voer de nieuwe waarde in. Leeg laten bij bewerken betekent momenteel dat de bestaande sleutel wordt behouden.
- **Uitschakelen na eerdere configuratie:** de huidige gebruikersinterface ondersteunt nog geen expliciete actie om een opgeslagen sleutel helemaal te verwijderen. Verwijder daarvoor niet handmatig bestanden onder `.storage`; dit vereist een nog te ontwikkelen veilige verwijderoptie.
- **Niet automatisch delen:** NeerslagKompas leest geen sleutels uit andere reeds geïnstalleerde KNMI-/Weerlive-integraties en deelt een sleutel nog niet automatisch tussen verschillende NeerslagKompas-configuraties.
- **Nooit publiceren:** plaats de API-sleutel niet in GitHub Issues, logs, screenshots, chatberichten of een publiek `.storage`-bestand. Bewaar sleutels in een wachtwoordmanager.
- **Foutmelding:** bijvoorbeeld `HTTP 403, stage list_files` betekent dat de eerste KNMI-aanvraag is geweigerd. Verifieer de sleutelsoort en toegangsrechten zonder de sleutel te delen.

## 4. Installatie en updates via HACS

Bekijk de [hoofdpagina](../README.md) voor de HACS-installatiestappen en het gebruiken van GitHub Releases. Let op: bij een private GitHub-repository kan standaard-HACS-installatie een 404 opleveren. Maak de repository alleen openbaar nadat je de volledige geschiedenis op mogelijke geheimen hebt gecontroleerd.

Bronnen: [KNMI Open Data API](https://developer.dataplatform.knmi.nl/open-data-api), [KNMI nieuws](https://developer.dataplatform.knmi.nl/news), [Weerlive API](https://weerlive.nl/delen.php).
