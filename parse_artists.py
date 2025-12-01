from parsers.artfacts import parser

af=parser()

r=af.get_artist("Amalia Ulman")
if r:
    dbdata={"type":r["type"],"subtype":r["subtype"],"media":r["media"],"movements":r["movements"],"nationality":r["nationality"],"birthyear",r["birthyear"]}


