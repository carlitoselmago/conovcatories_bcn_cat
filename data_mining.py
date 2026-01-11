from helpers import Helpers
from DB import DB
import pandas as pd

pd.set_option('display.float_format', '{:.2f}'.format)  # Shows 2 decimal places

exportfolder="web/data/"

H = Helpers()
DB = DB()

entitats=["CLT019","barcelona_crea","moniques"]
years=(2019,2023)
famoso_exhibitions=5

print()
print(":"*60)
print(":::: VISTA GENERAL :::::")
print(":"*60)
print()

for e in entitats:
    print("\n:::::",e,"::::::")
    rows=DB.pg_query(
            f"""
    SELECT 
        year,
        COUNT(CASE WHEN c.money > 0 THEN 1 END)   AS winners,
        COUNT(CASE WHEN c.money = 0 THEN 1 END)   AS not_winners,

        COUNT(CASE WHEN gender='Male' AND  c.money > 0 THEN 1 END)   AS male_winners,
        COUNT(CASE WHEN gender='Female' AND  c.money > 0 THEN 1 END)   AS female_winners,

        COUNT(CASE WHEN gender='Male' AND  c.money = 0 THEN 1 END)   AS male_not_winners,
        COUNT(CASE WHEN gender='Female' AND  c.money = 0 THEN 1 END)   AS female_not_winners,

        COUNT(CASE WHEN exhibitions>9 AND  c.money > 0 THEN 1 END)   AS famoso_winners,
        COUNT(CASE WHEN exhibitions<10 AND  c.money = 0 THEN 1 END)  AS not_famoso_not_winners
        FROM public.convocatoria c
        LEFT JOIN artists a ON a.id=c.artist 
        WHERE entitat='{e}'
        GROUP BY year
        ORDER BY year ASC
    ;"""
    )

    df=pd.DataFrame(rows, columns=DB.get_col_names())
    print(df.head())

    if e=="barcelona_crea":
     
        df=df._append({'year': 2022, 'winners': 60,'not_winners':900}, ignore_index=True)
    df.to_csv(exportfolder+f"vista_general_{e}.csv")

for e in entitats:
    print("\n:::::",e,"::::::")
    # Contar horas netas por convocatoria

    salario_hora=9.26
    media_dedicacion_horas=35

    """
    SELECT a.name,c.money FROM public.convocatoria as c
    LEFT JOIN artists as a ON c.artist=a.id
    WHERE entitat='CLT019' AND year=2025 

    ORDER BY c.id ASC 
    """

    """
    SELECT a.name,c.money FROM public.convocatoria as c
    LEFT JOIN artists as a ON c.artist=a.id
    WHERE entitat='CLT019' AND year=2025 

    ORDER BY c.id ASC 
    """

    rows=DB.pg_query(
        f"SELECT year as año,SUM(money) ganado,COUNT(*) as candidatos FROM convocatoria WHERE entitat='{e}' GROUP BY year ORDER BY year ASC;"
    )
    df = pd.DataFrame(rows, columns=DB.get_col_names())
    ganadores=DB.pg_query(
        f"SELECT year,COUNT(artist) as ganadores FROM public.convocatoria WHERE entitat='{e}' AND money>0 GROUP BY year ORDER BY year ASC"
    )

    
    df_ganadores=pd.DataFrame(ganadores, columns=DB.get_col_names())

    df["ganadores"]=df_ganadores["ganadores"]
    df["no ganadores"]=df["candidatos"]-df["ganadores"]

    #Calcular horas dedicadas a preparar los proyectos

    df["horas dosieres"] = df["candidatos"] * media_dedicacion_horas

    # Calculamos que las horas que debería dedicar un artista por el dinero ganado son:
    # (ganado / ganadores) / salario_hora = horas para producir

    #df["horas trabajo totales"] = (((df["ganado"].astype(float) / df["ganadores"].astype(float)) / salario_hora) *  df["ganadores"].astype(float) ) + (df["no ganadores"]*media_dedicacion_horas) * salario_hora
    df["horas produccion ganadores"] = ( df["ganado"].astype(float) / salario_hora )
    df["horas trabajo totales"] = df["horas dosieres"] + df["horas produccion ganadores"]
    df["horas realmente remuneradas"] = df["horas trabajo totales"] / df["ganado"].astype(float)

    # Compare: Are paid hours greater than preparation hours?
    #df["es_rentable"] = df["horas remuneradas totales"] > df["horas totales preparacion"]
    #df["diferencia_horas"] = df["horas remuneradas totales"] - df["horas totales preparacion"]


    print(df.head())

print()
print(":"*60)
print(":::: DESVIACION GENERO:::::")
print(":"*60)
print()
    
for e in entitats:
    print("\n:::::",e,"::::::")
    
    rows=DB.pg_query(
            f"""
                SELECT 
                c.year,
                COUNT(CASE WHEN a.gender = 'Male' THEN 1 END)   AS male_cand,
                COUNT(CASE WHEN a.gender = 'Female' THEN 1 END) AS female_cand,
                COUNT(CASE WHEN a.gender = 'Male' AND money>0 THEN 1 END)  AS male_win,
                COUNT(CASE WHEN a.gender = 'Female' AND money>0 THEN 1 END)  AS female_win
            FROM public.convocatoria c
            LEFT JOIN artists a ON c.artist = a.id
            WHERE c.entitat = '{e}'
            GROUP BY c.year
            ORDER BY c.year
    ;"""
    )
    df = pd.DataFrame(rows, columns=DB.get_col_names())

    df["desviacion_cand"]=df["male_cand"]-df["female_cand"] # positivo es hombre, negativo es mujer
    df["desviacion_win"]=df["male_win"]-df["female_win"]

    print(df.head())

    df.to_csv(exportfolder+f"desv_genero_{e}.csv")



print()
print(":"*60)
print(":::: POR ARTISTAS RECONOCIDOS:::::")
print(":"*60)
print()
    
for e in entitats:
    print("\n:::::",e,"::::::")
    
    """
      SELECT 
	c.year,
	COUNT(CASE WHEN a.rank = 'Top 10,000' THEN 1 END) AS TopA,
	COUNT(CASE WHEN a.rank = 'Top 100,000' THEN 1 END) AS TopB,
	COUNT(CASE WHEN a.rank = 'Top 1,000,000' THEN 1 END) AS TopC,
	COUNT(CASE WHEN a.rank is null THEN 1 END) AS nontop
	
    FROM public.convocatoria c
    LEFT JOIN artists a ON c.artist = a.id
    WHERE c.entitat = 'CLT019'
    GROUP BY c.year
    ORDER BY c.year
    """


    rows=DB.pg_query(
            f"""
                SELECT year,entitat,name,money,gender, exhibitions,rank FROM public.convocatoria c
LEFT JOIN artists a ON c.artist=a.id 
WHERE c.entitat='{e}'
ORDER BY c.id ASC 
    ;"""
    )
    df = pd.DataFrame(rows, columns=DB.get_col_names())

    # 1. keep only winners
    winners = df[df["money"] > 0].copy()

    # 2. classify known vs emerging
    winners["is_known"] = (
        winners["rank"].isin(["Top 10,000", "Top 100,000"]) |
        (winners["exhibitions"] >= 5)
    )

    # 3. aggregate per year
    summary = (
        winners
        .groupby("year")
        .agg(
            total_winners=("is_known", "size"),
            known_artists=("is_known", "sum")
        )
        .reset_index()
    )

    # 4. calculate percentage
    summary["pct_known_artists"] = (
        summary["known_artists"] / summary["total_winners"] * 100
    )

    print(summary.head())

    summary.to_csv(exportfolder+f"known_artists_{e}.csv")


# Shankey like, personaes que repiten convocatoria

print()
print(":"*60)
print(":::: ARTISTAS QUE REPITEN :::::")
print(":"*60)
print()
import pandas as pd
from collections import defaultdict

# --------------------------------------
# DATA (from your query)
# --------------------------------------

rows = DB.pg_query(
    """
    SELECT
        year,
        a.id AS person_id,
        entitat AS institution
    FROM public.convocatoria c
    LEFT JOIN artists a ON c.artist = a.id
    ORDER BY c.id ASC;
    """
)

df = pd.DataFrame(rows, columns=DB.get_col_names())

# --------------------------------------
# CLEANUP
# --------------------------------------

df = df.dropna(subset=["year", "person_id", "institution"])
df["year"] = df["year"].astype(int)
df["person_id"] = df["person_id"].astype(str)

institution_map = {
    "barcelona_crea": "Barcelona Crea",
    "clt019": "CLT019",
    "moniques": "Moniques"
}

df["institution"] = (
    df["institution"]
      .str.lower()
      .map(institution_map)
)

df = df.dropna(subset=["institution"])

# --------------------------------------
# CORE LOGIC: CONTINUOUS PERSISTENCE
# --------------------------------------

def compute_persistence(df_subset):
    """
    Returns a dataframe:
    year | streak | count | pct
    """
    person_years = (
        df_subset.groupby("person_id")["year"]
        .apply(lambda s: sorted(set(s)))
    )

    years = sorted(df_subset["year"].unique())
    counts = {year: defaultdict(int) for year in years}

    for person, ys in person_years.items():
        ys_set = set(ys)

        for year in ys:
            streak = 1
            prev = year - 1
            while prev in ys_set:
                streak += 1
                prev -= 1

            counts[year][streak] += 1

    # Build dataframe
    rows = []
    for year in years:
        total = sum(counts[year].values())
        for streak, c in counts[year].items():
            rows.append({
                "year": year,
                "streak": streak,
                "count": c,
                "pct": c / total * 100 if total > 0 else 0
            })

    return pd.DataFrame(rows)

# --------------------------------------
# COMPUTE:
# - total
# - per institution
# --------------------------------------

df_total = compute_persistence(df)
df_total["institution"] = "Total"

dfs = [df_total]

for inst in df["institution"].unique():
    df_inst = df[df["institution"] == inst]
    df_p = compute_persistence(df_inst)
    df_p["institution"] = inst
    dfs.append(df_p)

result = pd.concat(dfs, ignore_index=True)

# --------------------------------------
# FINAL SHAPE (JS-FRIENDLY)
# --------------------------------------
# Columns:
# year | institution | streak | pct

result = result[["year", "institution", "streak", "pct"]]

# Optional: cap streaks (e.g. 5+ years)
MAX_STREAK = 5
result["streak"] = result["streak"].apply(
    lambda x: x if x <= MAX_STREAK else MAX_STREAK
)

# Save for JS
result.to_csv("web/data/persistence_by_year_pct.csv", index=False)



# artists that tried and won

import pandas as pd

# -------------------------------------------------
# 1) LOAD DATA (your query)
# -------------------------------------------------

rows = DB.pg_query(
    """
    SELECT
        year,
        a.id AS person_id,
        a.name AS name,
        entitat AS institution,
        money
    FROM public.convocatoria c
    LEFT JOIN artists a ON c.artist = a.id
    ORDER BY c.id ASC;
    """
)

df = pd.DataFrame(rows, columns=DB.get_col_names())

# -------------------------------------------------
# 2) BASIC CLEANUP
# -------------------------------------------------

df = df.dropna(subset=["year", "person_id"])
df["year"] = df["year"].astype(int)
df["person_id"] = df["person_id"].astype(str)

# Define "win" (adjust if your schema differs)
df["is_win"] = df["money"].notna() & (df["money"] > 0)

# -------------------------------------------------
# 3) AGGREGATE PER ARTIST (SAFE VERSION)
# -------------------------------------------------

def summarize_artist(group):
    return pd.Series({
        "total_applications": len(group),
        "years_applied": group["year"].nunique(),
        "first_year": group["year"].min(),
        "last_year": group["year"].max(),
        "total_wins": int(group["is_win"].sum()),
        "years_won": sorted(group.loc[group["is_win"], "year"].unique())
    })

artist_summary = (
    df.groupby(["person_id", "name"], dropna=False)
      .apply(summarize_artist)
      .reset_index()
)

# -------------------------------------------------
# 4) FILTER: TRIED MORE THAN ONCE AND WON
# -------------------------------------------------

persistent_winners = artist_summary[
    (artist_summary["years_applied"] > 1) &
    (artist_summary["total_wins"] > 0)
].sort_values(
    ["years_applied", "total_wins"],
    ascending=False
)

# -------------------------------------------------
# 5) OPTIONAL: ADD YEARS UNTIL FIRST WIN
# -------------------------------------------------

first_win_year = (
    df[df["is_win"]]
    .groupby("person_id")["year"]
    .min()
    .rename("first_win_year")
)

persistent_winners = (
    persistent_winners
    .set_index("person_id")
    .join(first_win_year)
    .reset_index()
)

persistent_winners["years_until_first_win"] = (
    persistent_winners["first_win_year"] - persistent_winners["first_year"]
)

# -------------------------------------------------
# 6) SANITY CHECKS (PRINT NUMBERS)
# -------------------------------------------------

print("Total artists:", artist_summary.shape[0])
print("Artists who applied more than once:",
      (artist_summary["years_applied"] > 1).sum())
print("Artists who won at least once:",
      (artist_summary["total_wins"] > 0).sum())
print("Artists who applied more than once AND won:",
      persistent_winners.shape[0])

print("\nPreview of persistent winners:\n")
print(
    persistent_winners[
        [
            "name",
            "years_applied",
            "total_applications",
            "total_wins",
            "years_won",
            "years_until_first_win"
        ]
    ].head(10)
)

# -------------------------------------------------
# 7) (OPTIONAL) EXPORT
# -------------------------------------------------

# persistent_winners.to_csv("persistent_winners.csv", index=False)





DB.pg_close()