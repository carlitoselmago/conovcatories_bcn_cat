# conovcatories_bcn_cat
Código para la minería de datos de convocatorias en Barcelona - Catalunya

## Fuentes de datos
- https://tauler.seu-e.cat/inici
- https://bop.diba.cat/resultats-cerca?bopb_cerca%5BdataInici%5D=29-08-2025&bopb_cerca%5BdataFinal%5D=29-11-2025&bopb_cerca%5BparaulaClau%5D=barcelona%20crea

## Fuentes complementarias
- https://artfacts.net/
- https://huggingface.co/padmajabfrl/Gender-Classification

## Convocatorias analizadas
- Barcelona Crea (2020-2025)
- Becas para la creación artística, la investigación y la innovación en los ámbitos de las artes visuales, escénicas, música, pensamiento y juegos de mesa (2019-2025)
- Subvenciones para proyectos artísticos de carácter profesional en el ámbito de las artes visuales (2019-2025)

Pendiente de completar el listado con convocatorias como Barcelona Producció (La Capella)

# Entidades de datos
- convocatoria
- candidato

# Instalación
```
sudo apt install poppler-utils
sudo apt install firefox-esr
sudo apt install python3-selenium
wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz
tar -xzf geckodriver-*.tar.gz
sudo mv geckodriver /usr/local/bin/
sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \

# Descargar el modelo OCR desde: https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/blob/d4cebcc544ac0c9899748e1023e2f3ccda8ca70e/model_final.pth?utm_source=chatgpt.com

# Archivo de configuración: : https://www.dropbox.com/s/f3b12qc4hc0yh4m/config.yml?dl=1

pip install -r requirements.txt

# Configurar la clave de OPENAI con:
export OPENAI_API_KEY={yourkey}
```

# Compatibilidad
Probado en Linux Zorin, Python 3.11.10


# Pasos de procesado
- Primero he descargado manualmente los pdfs de cada resolución
- Luego he utilizado OCR para convertir cada tabla a csv con process_pdf.py
- Luego he limpiado y enriquecido los datos con process_cs.py, los datos pasan entonces a una base de datos local de postgres
- Para terminar he hecho una revisión manual para clasificar colectivos por su nombre (incluyen la palabra 'cole')