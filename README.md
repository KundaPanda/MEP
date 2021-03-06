# Systém pro kontrolu vstupenek s využítím QR kódů

## Getting started:
0. Have up-to-date linux distro
1. Have [docker](https://docs.docker.com/install/) installed
2. Run: "source run.sh"
3. Use "export-data" and "import-data" to for migrating your entire database

## TODO:
* add reverse proxy to docker
* admin UI
* licence?
* http cesty (/db/ /db/table/ ) ... testy?
* dokumentace obsahu postgres
* dokumentace trid/metod

## Součásti aplikace:
* api
  * **pip:** flask, psycopg2, APScheduler, qrcode, beautifulsoup4, flask_basicauth
  * python 3.7+
* nginx
  * reverse proxy
    * authentizace uzivatelu
    * https (ne lokalni)
  * webové rozhraní pro správu (jako "statická stránka")
    * využívá volání /api/ui/*
    * vytvareni uzivatelu
    * export tiskove sestavy
    * export dat?
    * html + css + angular.js
* postresql
  * vsechna data zde
* klientska aplikace
  * pro system Android 7.x+
  * prihlaseni uzivatele
  * dekodovani qr kodu
  * overeni dekodovaneho qr kodu pomoci /api/check

## Testovácí strategie:
* Porovnávání výstupu API s referenčním výstupem z dokumentace (automatizované (hashe?)
* Android aplikace testována pomocí sady qr kodu
* Webové rozhraní testováno manuálně (automatizace pro tento rozsah by byal neefektivní)
* + testování zátěže (skrz proxy)
* + test úspěšného obnovení z exportu/zálohy
