import pandas as pd
from helpers import Helpers

H = Helpers()

file = "output.csv"
df = pd.read_csv(file)

print(df.head())

# Prepare new empty columns
df["gender"] = None
df["gender_score"] = None

# Initialize classifier
H.init_genderClass()

# Process gender for each row
for index, row in df.iterrows():

    if "*" in row["NIF"]:
        # It is not a collective
        name = row["Nom"]
        print("Processing:", name)

        pred = H.predictGender(name)   


        gender = pred["label"]
        gender_score = pred["score"]
    
        df.at[index, "gender"] = gender
        df.at[index, "gender_score"] = gender_score
    else:
        df.at[index, "gender"] = None
        df.at[index, "gender_score"] = 0.0

# Save the updated file
df.to_csv("output_with_gender.csv", index=False)

print("\n=== Updated DF ===")
print(df.head())


# -------- GLOBAL GENDER COUNTS --------
count_male = (df["gender"] == "Male").sum()
count_female = (df["gender"] == "Female").sum()
count_none = df["gender"].isna().sum() + (df["gender"] == "none").sum()

print("\n=== GLOBAL Gender Counts ===")
print("Male:   ", count_male)
print("Female: ", count_female)
print("None:   ", count_none)


# -------- GROUPED BY RESOLUCIÓ --------
df_true = df[df["Resolució"] == True]
df_false = df[df["Resolució"] == False]

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