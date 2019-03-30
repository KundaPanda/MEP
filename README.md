# Systém pro kontrolu vstupenek s využítím QR kódů

## Součásti aplikace:
* api
  * python 3.7+
  * komunikace s postgresql
  * nedrzi v sobe zadna data (stateless)
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

## Testování:
* zatezove testovani api (i s reverse proxy)
* postman
* ???

## TODO:
* requirements.txt formát!?
* dokumentace obsahu postgres
* dokumentace trid/metod
* smazat kotatka?
* jaka licence?