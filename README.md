# Häkki — HTML-katalogi

Paikallinen, offline-toimiva selailukatalogi `list`-tiedoston 208 laiteriville.

## Tiedostot

- `katalogi.html` — valmis katalogi (yksi HTML + paikallinen `assets/`-kansio, ei ulkoisia resursseja)
- `assets/commons/` — ladatut Wikimedia Commons -pikkukuvat + `images.json` (attribuutio- ja lisenssimetadata)
- `list` — lähde (älä muuta; katalogi lukee siitä kuvaukset ja linkit rakennusvaiheessa)
- `build_katalogi.py` — generaattori, jolla `katalogi.html` on tehty
- `fetch_commons.py` — Commons-haku (API + lisenssit + lataus, osuvuussuodatus, poissulkulista)
- `manual_add.py` — käsin kuratoidut täydennykset
- `README.md` — tämä ohje

## Käyttö

1. Avaa `katalogi.html` selaimessa (tuplaklikkaa tai `python3 -m http.server` + selaimeen `http://127.0.0.1:PORT/katalogi.html`).
2. Hae tekstillä, suodata kategorialla (A–K), reitillä (S/F/H/E), vaikeudella (1–5) ja kehoroolilla.
3. Vaihda teemaa: Vaalea / Tumma / Kontrasti (tallentuu selaimeen).
4. Jokaisesta kortista: kuvaus + lähdelinkki (Projekti/docs) alkuperäiseen dokumentaatioon.

## Kuvat / attribuutio — todellinen tilanne

- **194 / 203 yksilöllisestä laitemallista (208 riviä) on paikallinen Wikimedia Commons -kuva** kansiossa `assets/commons/` (166 tiedostoa; samat mallit jakavat kuvan).
- **9 mallia jäi ilman varmennettua osumaa ja näytetään selkeänä placeholderina** (`Kuva puuttuu` -merkintä kortissa): WowWee MiP, Petoi Bittle/Nybble (legacy + X), Korg NTS-1, Duet/RepRapFirmware, FluidNC, Crazyflie 2.x, EdgeTX-lähettimet, yleiset tietoturvetietokoneet. Näille korteissa on Wikimedia/Openverse-haut.
- Jokaista kuvaa käytetään vain, jos Commons-tiedoston nimi täsmää laitteen tunnisteeseen (token-osuvuus + poissulkulista ihmisille, paikoille, eläimille, ajoneuvoille ja väärille malleille). Kortti näyttää aina todellisen Commons-tiedostonimen, tekijän, lisenssin ja lähdesivun — placeholderia ei koskaan väitetä tuotekuvaksi.
- **Tarkista kuvan lisenssi (`images.json`: `license`, `license_url`) ennen uudelleenkäyttöä ja merkitse tekijä.** Osa kuvista on esim. CC BY-SA -lisenssillä.
- Kuvat on haettu Commons APIsta (hakutulokset + `extmetadata`-lisenssit) ja ladattu paikallisesti 320–640px pikkukuvina; ei hotlinkkausta.

## Uudelleenrakennus

```bash
python3 fetch_commons.py     # päivittää assets/commons/images.json (verkko + kohteliaisuusviiveet)
python3 manual_add.py        # kuratoidut täydennykset
python3 build_katalogi.py    # kirjoittaa katalogi.html uudelleen
```

Lukee `list`-tiedoston katalogiosion (`## The catalog` … `## Tools`). Ei koske `list`-lähdettä.

## Testit

- Rivimäärä: `list`-katalogiosiossa 208 taulukkoriviä → `katalogi.html` sisältää 208 korttia (`DATA`-taulukko).
- Kaikilla 208 rivillä on kuvaus + lähdelinkki; kuvatiedostot tarkistettu (JPEG/PNG/WebP-magic, ei virussivuja).
- Offline: ei `<link>`/`<script src>`/`img src=http>`-riippuvuuksia; kuvat ovat paikallisia `assets/`-polkuja (vain projekti/kuvahaut-linkit vievät ulos).
