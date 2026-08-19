#!/usr/bin/env python3
"""Apply the Bellefair hook card to all 15 -> finals_ig/<id>_..._ig.mp4"""
import sys, ig_hook
HOOKS={
 1:["Claude Is","Blind And Deaf"],
 2:["AI Runs My","Instagram 24/7"],
 3:["How People","Spot Your AI"],
 4:["Microsoft Is","Burning You Out"],
 5:["Microsoft Is","A C-Player"],
 6:["Managing People","Is A Nightmare"],
 7:["Stop Saying","“I Can’t Afford It”"],
 8:["You Can’t Scale","Without Sales"],
 9:["Most People","Get Cold Feet"],
 10:["You Were Trained","To Need A Job"],
 11:["Your Bank Is","Scamming You"],
 12:["Trump Showed Us","The Future Of Money"],
 13:["My Family Thought","I Got Hacked"],
 14:["Social Media Is","More Real Than Life"],
 15:["Men & Women","Chase Money Differently"],
}
ids=[int(x) for x in sys.argv[1:]] if len(sys.argv)>1 else list(HOOKS)
ok=0
for cid in ids:
    if ig_hook.composite_ig(cid,HOOKS[cid]): ok+=1
print(f"IG done {ok}/{len(ids)}")
