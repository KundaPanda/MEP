# IB053 Systém kontroly vstupu s využitím QR kódů

## Cile:
Systém pro kontrolu (a generování) vstupenek s QR kódy.<br>

### Komponenty a základní funkcionalita:
  * API pro ověření vstupenek a pro webové rozhraní
    * s autentizací pomocí reverse proxy (python, flask)
    * jednotlivé metody specifikovány v příloze (papír1)
  * webové rozhraní pro inicializaci a základní správu (angular.js)
    * autentizace opět pomocí reverse proxy
    * inicializace databáze a uživatelů
    * export tiskové sady (generované pomocí API)
  * android aplikace pro načítání QR kódů (kotlin)
    * korektní načtení QR kódu
    * ověření pomocí API
    * zobrazení výsledku

Nasazení všech komponent, databáze a reverse proxy jako docker kontejnerů.<br>
Použitou databází bude postresql.<br>

## Práce na součástech projektu:
Výběr knihoven pro jednotlivé části/komponenety je svěřen jejich autorům.<br>

* Vojtěch Dohnal
  * android aplikace
  * api
* Ondřej Malaník
  * webové rozhraní
* Ondřej Molík
  * nastavení reverse proxy, dockeru
  * sepsání dokumentace + testování
  * co ještě bude potřeba

## Testovácí strategie:
* Porovnávání výstupu API s referenčním výstupem z dokumentace (automatizované (hashe?)
* Android aplikace testována pomocí sady qr kodu
* Webové rozhraní testováno manuálně (automatizace pro tento rozsah by byal neefektivní)
* + testování zátěže (skrz proxy)
* + test úspěšného obnovení z exportu/zálohy

Všeobecně se počítá s využitím principů agilního vývoje, z důvodů našich menších zkušeností s takovýmito projekty.<br>