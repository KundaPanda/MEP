# Systém pro kontrolu vstupenek s využítím QR kódů

**!!! odstraneno api/install_requiments... místo něj používat "pip install -r api/requirements.txt" !!!**<br>
**!!! psycopg2 nahrazeno psycopg2-binary, neni nutne instalovat postgresql-client, balicek jej jiz obssahuje !!!**<br>

## TODO:
* **incializace postgres do shell scriptu (z textu to neni moc deterministicky)**
* licence?
* http cesty (/db/ /db/table/ )?
* dokumentace obsahu postgres
* dokumentace trid/metod

## Součásti aplikace:
* api
  * **pip:** flask, psycopg2-binary, APScheduler, qrcode, beautifulsoup4, flask_basicauth, shutil
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

