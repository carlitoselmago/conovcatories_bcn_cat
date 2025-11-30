import pymupdf
from pprint import pprint
import re
import pymupdf4llm
import pandas as pd
import os
from pathlib import Path
import glob

from helpers import Helpers
H=Helpers()

for root, dirs, files in os.walk("resolucions"):
    for file in files:
        if file.lower().endswith(".pdf"):
            print("")
            print("######################")
            print("######################")
            print("######################")
            print("######################")
            print("Procesing file:")
            print(root,file)

            #PARSE
            md_text = pymupdf4llm.to_markdown(os.path.join(root, file))

            table_step=0

            atorgades=[]
            denegades=[]

            for line in md_text.splitlines():
                line=line.strip()
                print(line)
                if line!="" and "|" in line:
                    if "|NIF|Nom/RaóSocial|Denominació|Modalitat|ExpedientGPA|Puntuació|Resolució|Import" in line:
                        table_step=1
                        continue
                    if "NIF|Nom/RaóSocial|Denominació|Modalitat|ExpedientGPA|" in line and table_step==1:
                        table_step=2
                        continue
                        
                    if "|---|---|---|---|---|" not in line:

                        fields=line.split("|")
                        fields_clean=[]
                        for f in fields:
                            f=f.strip()
                            if f!="":
                                f=f.replace("<br>"," ")
                                f=f.replace("_ _","")
                                fields_clean.append(f)
                        
                        nones=fields_clean.count(None)
                        print("nones",nones)
                        if nones>7:
                            continue
                        print(fields_clean)
                        # Adjuntments on different column orders
                        if "2023" in file:
                            reordering={0:0,1:1,2:2,3:4,4:3,5:5,7:6,6:7}
                            fields_clean=H.reorder_with_map(fields_clean,reordering)
                        print(fields_clean)

                        #clean up numbers :::::

                        # Money
                        fixed_number = H.cleanup_number(fields_clean[-1])
                        if fixed_number is not None:
                            fields_clean[-1] = fixed_number
                        else:
                            pass
                            #print("Could not convert number:", fields_clean[-1])
                                
                        try:
                            if fields_clean[-1]>8000:
                                fields_clean[-1]=float(6000)
                        except:
                            pass

                        # Punts
                        fields_clean[5]=H.cleanup_punts(fields_clean[5])

                        if "Col" in fields_clean[0]:
                            continue

                        if table_step==1:
                            pass
                            # Atorgats table
                            #print(fields_clean)
                            atorgades.append(fields_clean)
                            #print(line)

                        if table_step==2:
                            if fields_clean[0]=="NIF":
                                continue
                            print(fields_clean)
                            denegades.append(fields_clean)
                

            print(len(atorgades))
            print(len(denegades))

            #Save csv
            # Combine the lists of lists
            all_rows = atorgades + denegades


            

            columns=["NIF","Nom","Denominació","Modalitat","Expedient","Puntuació","Resolució","Import"]

            # Create DataFrame
            df = pd.DataFrame(all_rows, columns=columns)


            # post processing :::::

            # Convert resolucio into binary
            df["Resolució"]=df["Resolució"].str.contains("Atorgada", case=False, na=False)



            # Save to CSV


            # Build new directory by replacing the prefix
            out_dir = root.replace("resolucions/", "data/")

            # Ensure directory exists
            os.makedirs(out_dir, exist_ok=True)

            # Build filename safely
            base = Path(file).stem
            outfile = base + ".csv"

            # Final path
            outputfile = os.path.join(out_dir, outfile)
            print(outputfile)
            
            df.to_csv(outputfile, index=False)

            print(df)
