import pandas as pd
import numpy as np
from helpers import Helpers
from parsers.artfacts import parser
from DB import DB
import pathlib
import os
from time import sleep

H = Helpers()
DB = DB()
af=parser()

# Initialize classifier
H.init_genderClass()

#root="data/CLT019/2019/"
#file = "ANNEX.csv"

root="data/barcelona_crea/2025/"
file = "ANNEX 3.csv"

df = pd.read_csv(
    os.path.join(root, file),
    engine="python",
    quoting=3,      
    sep=None,     
    on_bad_lines="skip"
)

# prefix values based on convo
pathparts=pathlib.Path(root).parts

entitat=str(pathparts[1])
year=int(pathparts[2])
df["entitat"]=entitat

# Prepare new empty columns
df["gender"] = None
df["gender_score"] = None
df["artist"] = None
df["iscollective"]=False


if entitat=="CLT019":
    df=df.rename({'Import':'money', 'Identificació beneficiari':'dni', 'Descripció acció':'project', 'Motius':'reason',"Tipus d'acord":"granted"}, axis='columns')
    grantedstr="Concedit"
    df["score"]=0.0
    df["artistname"] =""

if entitat=="barcelona_crea":
    df=df.rename({'Nom/Raó Social':"artistname",'Import atorgat':'money', 'NIF':'dni', 'Denominació':'project', 'Resolució':'granted',"Puntuació Total":"score","Modalitat":"category"}, axis='columns')
    df["reason"]=df["granted"].astype(str)

    grantedstr="Atorgada"

# Convert granted to bool
df["granted"] = df["granted"].astype(str).str.contains(grantedstr, case=False, na=False)


# Convert score to numeric
df["score"] = (
    df["score"]
    .astype(str)
    .str.replace(".", "", regex=False)  
    .str.replace(",", ".", regex=False) 
    .str.strip()
)

df["score"] = pd.to_numeric(df["score"], errors="coerce")

# Convert money to float
df["money"] = (
    df["money"]
    .astype(str)
    .str.replace("€", "", regex=False)
    .str.replace(".", "", regex=False)   
    .str.replace(",", ".", regex=False) 
    .str.strip()
    .astype(float)
)

# Cleanup possible mistakes in reason
df["reason"] = df["reason"].apply(lambda x: np.nan if H.is_mostly_numeric(x) else x)

# Keep only the relevant columns
cols_to_keep=["dni","artistname","project","granted","score","money","reason","gender","gender_score","artist","category","iscollective"]
df = df[cols_to_keep]


print(df.head())


# Now lets process the artist

# Process gender for each row
for index, row in df.iterrows():

    name = row["artistname"]
    dni = row["dni"]

    if "*" in row["dni"]:
        # It is not a collective
        
        if name!="":
            print("Processing:", name)
            pred = H.predictGender(name)   

            gender = pred["label"]
            gender_score = pred["score"]
        
            df.at[index, "gender"] = gender
            df.at[index, "gender_score"] = gender_score
    else:
        df.at[index, "gender"] = None
        df.at[index, "gender_score"] = 0.0
        if entitat=="barcelona_crea":
            df.at[index, "iscollective"] = True

    artistname=name
    
    artist_id, existed = DB.add_artist(artistname, dni,df.at[index, "iscollective"])
    print("Artist ID:", artist_id, "Already existed:", existed)
   
    if artistname!="":
        r=af.get_artist(artistname)

        sleep(2)
        if r:
            dbdata = {
            "type": r["type"],
            "subtype": r["subtype"],
            "media": r["media"],
            "movements": r["movements"],
            "nationality": r["nationality"],
            "birth_year": r["birth_year"],
            "rank": r["rank"],
            "exhibitions": r["exhibitions"],
            "gender": r["gender"]
            }
        else:
            dbdata={
                "gender": df.at[index, "gender"],
                "gender_score": df.at[index, "gender_score"]
            }
        DB.update_artist(artist_id, dbdata)

    # Set artist in the row with it's id
    df.at[index,"artist"]=artist_id
    row["artist"]=artist_id
    
    # Save convocatoria unit
    convo_row={"artist":row["artist"],"granted":row["granted"],"money":row["money"],"year":year,"score":row["score"],"reason":row["reason"],"entitat":entitat,"project":row["project"]}
    DB.add_convocatoria(convo_row)

print(df.head())


"""
# Save the updated file
df.to_csv("output_with_gender.csv", index=False)

print("\n=== Updated DF ===")
print(df.head())
"""

# -------- GLOBAL GENDER COUNTS --------
count_male = (df["gender"] == "Male").sum()
count_female = (df["gender"] == "Female").sum()
count_none = df["gender"].isna().sum() + (df["gender"] == "none").sum()

print("\n=== GLOBAL Gender Counts ===")
print("Male:   ", count_male)
print("Female: ", count_female)
print("None:   ", count_none)


# -------- GROUPED BY RESOLUCIÓ --------
df_true = df[df["granted"] == True]
df_false = df[df["granted"] == False]

def gender_counts(group):
    return {
        "Male":   (group["gender"] == "Male").sum(),
        "Female": (group["gender"] == "Female").sum(),
        "None":   group["gender"].isna().sum() + (group["gender"] == "none").sum()
    }

counts_true = gender_counts(df_true)
counts_false = gender_counts(df_false)

print("\n=== Gender Counts (Resolució = TRUE) ===")
print("Male:   ", counts_true["Male"])
print("Female: ", counts_true["Female"])
print("None:   ", counts_true["None"])

print("\n=== Gender Counts (Resolució = FALSE) ===")
print("Male:   ", counts_false["Male"])
print("Female: ", counts_false["Female"])
print("None:   ", counts_false["None"])