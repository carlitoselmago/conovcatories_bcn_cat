# conovcatories_bcn_cat
Codi per la mineria de dades de convocatòries a Barcelona - Catalunya

## Fonts de dades
- https://tauler.seu-e.cat/inici
- https://bop.diba.cat/resultats-cerca?bopb_cerca%5BdataInici%5D=29-08-2025&bopb_cerca%5BdataFinal%5D=29-11-2025&bopb_cerca%5BparaulaClau%5D=barcelona%20crea

## Fonts complementàries
- https://artfacts.net/
- https://huggingface.co/padmajabfrl/Gender-Classification

## Convocatòries analitzades
- Barcelona Crea (2020-2025)
- Beques per a la creació artística, la recerca i la innovació en els àmbits de les arts visuals, de les arts escèniques, de la música, del pensament i dels jocs de taula (2019-2025)
- Subvencions per a projectes artístics de caràcter professional en l’àmbit de les arts visuals (2019-2025)

A l'espera de completar el llistat amb convocatóries com la de Barcelona Producció (La Capella)

# Entitats de dades
- convocatoria
- candidat

# Instal·lació
```
sudo apt install poppler-utils
sudo apt install firefox-esr
sudo apt install python3-selenium
wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz
tar -xzf geckodriver-*.tar.gz
sudo mv geckodriver /usr/local/bin/
pip install -r requirements.txt
```

# Comptaibilitat
Testejat a linux zorin, Python 3.11.10