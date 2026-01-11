from helpers import Helpers
from DB import DB

exportfolder="web/data/"

H = Helpers()
DB = DB()

# Fix cantidades, cuando money=80000 en lugar de 8000

DB.pg_execute(
    "UPDATE convocatoria SET money=8000.0 WHERE money=80000.0"
)
DB.pg_execute(
    "UPDATE convocatoria SET money=6000.0 WHERE money=60000.0"
)
DB.pg_execute(
    "UPDATE convocatoria SET money=6000.0 WHERE money=66000.0"
)

# cas CLT019 2021, hi han projectes que tenen " Puntuació inferior a la mínima exigida, d'acord amb el punt 10.4 de les bases generals" pero que reben el diners
DB.pg_execute(
    "UPDATE convocatoria SET money=0 WHERE reason LIKE '%tzació inferior%'"
)



DB.pg_close()