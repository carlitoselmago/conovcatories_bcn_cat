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


for root, dirs, files in os.walk("data"):
    for file in files:
        if file.lower().endswith(".csv"):
            if "done" not in file:
                

                print("")
                print("######################")
                print("######################")
                print("Procesing file:")
                print("Folder:",root,"file:",file)
                print("")

                #root="data/moniques/2025/"
                #file = "RELACIÓ DE SOL·LICITUDS DESESTIMADES.csv"

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
                    replacecols={'Import':'money', 'Descripció acció':'project', 'Motius':'reason',"Tipus d'acord":"granted"}
                    if "Identificaci" in " ".join(df.columns):
                        replacecols['Identificació beneficiari']='dni'
                        df["artistname"] =""
                    else:
                         replacecols["Nom beneficiari"]="artistname"
                         df["dni"]=None
                    df=df.rename(replacecols, axis='columns')
                    grantedstr="Conce"
                    df["score"]=0.0
                    df["category"] = None

                    # fix name order
                    if year>2019:
                        df["artistname"]=df["artistname"].apply(H.normalize_name)
                    
                    
                if entitat=="barcelona_crea":
                    if "Import atorgat" in " ".join(df.columns):
                        #Han ganado
                        df=df.rename({'Nom/Raó Social':"artistname",'Import atorgat':'money', 'NIF':'dni', 'Denominació':'project', 'Resolució':'granted',"Puntuació Total":"score","Modalitat":"category"}, axis='columns')
                        #df["granted"]=True
                    else:
                        #No han ganado
                        df=df.rename({'Nom/Raó Social':"artistname", 'NIF':'dni', 'Denominació':'project', 'Resolució':'granted',"Puntuació Total":"score","Modalitat":"category"}, axis='columns')
                        #df["granted"]=False
                        df["money"]=0
                        #if "granted" not in " ".join(df.columns):
                        #    df["granted"]=False
                        #    print(df["granted"])
                    try:
                        df["reason"]=df["granted"].astype(str)
                    except:
                        df["granted"]=False
                        df["reason"]=df["granted"].astype(str)
                    #df["score"]=0.0
                    df["artistname"]=df["Nom"]
                    df["category"]=None
                    grantedstr=["Atorgada","Aprovada"]

                if entitat=="moniques":
                    if "licitant" in " ".join(df.columns):
                        df=df.rename({'Nom sol·licitant':"artistname", 'Identificació sol·licitant':'dni',"Descripció acció":"category"}, axis='columns')
                    else:
                        df=df.rename({'Nom beneficiari':"artistname", 'Identificació beneficiari':'dni',"Descripció acció":"category"}, axis='columns')

                    
                    df["score"]=0.0
                    df["project"]=""
                    if year==2021:
                        df = df.drop('project', axis=1)
                        df=df.rename({'category':'project'}, axis='columns')
                        df["category"]=""
                    df["granted"]=None
                    df["money"]=0
                    if "DESESTIMA" in file:
                        df["granted"]=False
                    if "CONCEDIDES" in file:
                        df["granted"]=True
                        df["money"]=9200
                    df["reason"]=""
                    money_granted=92000


                if  entitat!="moniques": 
                    # Convert granted to bool
                    if isinstance(grantedstr, str):
                        patterns = [grantedstr]
                    else:
                        patterns = grantedstr

                    df["granted"] = df["granted"].astype(str).apply(
                        lambda x: any(p.lower() in x.lower() for p in patterns)
                    )

                    # If at least one was true
                    if not df["granted"].any():
                        # Force money to be 0
                        df["money"] = 0


                # Convert score to numeric
                print(df.head())
                df["score"] = (
                    df["score"]
                    .astype(str)
                    .str.replace(r'\.(?=.*\.)', '', regex=True)
                    .str.replace(',', '.', regex=False)
                    .str.strip()
                )

                df["score"] = pd.to_numeric(df["score"], errors="coerce")

                # Convert money to float
                df["money"] = df["money"].apply(H.fix_money_value)
                """
                df["money"] = (
                    df["money"]
                    .astype(str)
                    .str.replace('"', "", regex=False)
                    .str.replace("€", "", regex=False)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.strip()
                    .replace("", np.nan)     # avoid converting empty strings
                    .astype(float)
                )
                """

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

                    iscollective=False
                      
                    val = row["dni"]

                    if entitat=="barcelona_crea":
                        if "*" not in val:
                            iscollective=True

                    #if not isinstance(val, str) or "*" not in val:
                    #    iscollective = True
                    #print("name",name,"iscollective",iscollective,val)
                    if not iscollective:
                        # It is not a collective
                        
                        if name!="":
                            
                            pred = H.predictGender(name)   

                            gender = pred["label"]
                            gender_score = pred["score"]
                        
                            df.at[index, "gender"] = gender
                            df.at[index, "gender_score"] = gender_score
                            print("Processing:", name,"GENDER:",gender)
                    else:
                        # it is a collective

                        df.at[index, "gender"] = None
                        df.at[index, "gender_score"] = 0.0
                        #if entitat=="barcelona_crea":
                        df.at[index, "iscollective"] = True

                    if entitat=="moniques":
                        # Set money and granted
                        if "ONCEDIDES" in file:
                            df.at[index, "money"]=money_granted
                            df.at[index, "granted"]=True
                        else:
                            df.at[index, "money"]=0
                            df.at[index, "granted"]=False

                    artistname=name
                    
                    artist_id, existed = DB.add_artist(artistname, dni,df.at[index, "iscollective"])
                    print("Artist ID:", artist_id, "Already existed:", existed)

                    
                    if not existed:

                        if artistname!="":
                            r=af.get_artist(artistname)
                            if r:
                                if "rank" not in r:
                                    r["rank"]=None
                                if "exhibitions" not in r:
                                    r["exhibitions"]=0
                                if "gender" not in r:
                                    r["gender"]=None
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
                    convo_row={"artist":row["artist"],"granted":row["granted"],"money":row["money"],"year":year,"score":row["score"],"reason":row["reason"],"entitat":entitat,"project":row["project"],"category":row["category"]}
                    
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

                #rename pdf with _done
                csv_path = os.path.join(root, file)
                done_pdf = csv_path.replace(".csv", "_done.csv")
                os.rename(csv_path, done_pdf)  

                print("FINISHED::::")
                print(root,":::",file)
                print()
                print()
                # Stop to check the next one
                for i in range(6):
                    os.system( 'echo -e "\007"' )
                    sleep(0.1)
                
                print(":::::::::::::::::::::::::::::::::::")
                print("END processing",file)
                print(":::::::::::::::::::::::::::::::::::")
                print()
                sleep(10)
                #sys.exit()