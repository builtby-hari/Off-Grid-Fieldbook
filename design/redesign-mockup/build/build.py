import json,sys,re
S=sys.argv[1]
src=open(S+'/fieldbook-redesign.src.html').read()
P=json.load(open(S+'/pick.json'))
d=json.load(open('REPO/content/library/search-index.json'))
N=lambda s: re.sub(r'\s+',' ',s)
IDX={(x['t'],x.get('p')):N(x['x']) for x in d}
def take(doc,p,start,n=430,end=None):
    # a real, unbroken stretch of the manual page, cut back to the end of a sentence
    t=IDX[(doc,p)]; i=t.index(start)
    if end: return t[i:t.index(end,i)+len(end)]
    s=t[i:i+n]; j=max(s.rfind('. '),s.rfind('.) '),s.rfind('! '))
    return s[:j+1] if s[-1] not in '.!)' else s
W='Where There Is No Doctor'; H='All Hazard Sheets (full set)'
t=IDX[(W,143)]; i=t.find('BURNS')
P.append({'id':'m19','doc':W,'h':'Burns','p':143,'x':t[i+6:i+6+420].rsplit(' ',1)[0],'w':1})
# sample pages added so the emergency screens and common searches quote the right manual
P.append({'id':'m20','doc':H,'h':'Tornado: survive during','p':27,'x':take(H,27,'Immediately go to a safe location'),'w':1})
P.append({'id':'m21','doc':H,'h':'Earthquake: survive during','p':9,'x':take(H,9,'Drop, Cover, and Hold On like you practiced.'),'w':1})
P.append({'id':'m22','doc':W,'h':'Fever','p':122,'x':take(W,122,'When a person’s body temperature is too hot',end='especially in a small child.'),'w':1})
P.append({'id':'m23','doc':W,'h':'Treatment for poisonous snakebite','p':152,'x':take(W,152,'1. Stay quiet'),'w':1,'kw':'snake bite'})
P.append({'id':'m24','doc':W,'h':'When something gets stuck in the throat','p':126,'x':take(W,126,'When food or something else sticks',n=520),'w':1,'kw':'choking choke'})
P.append({'id':'m25','doc':W,'h':'To prevent or treat dehydration','p':199,'x':take(W,199,'When a person has watery diarrhea',end='foods he likes and accepts.'),'w':1,'kw':'diarrhea rehydration drink dehydration'})
def clean(s):
    # tidy text-extraction leftovers; the words themselves are not changed
    s=s.replace('m ust','must').replace('—',', ').replace('–','-')
    s=re.sub(r'[•♦]',' ',s); s=re.sub(r'PRECAUTIONS:\s+(?=[A-Z])','PRECAUTIONS: ',s)
    return re.sub(r'\s+',' ',s).replace(' ,',',').strip()
for p in P: p['x']=clean(p['x']); p['h']=clean(p.get('h') or '')
SC=json.load(open(S+'/scen.json'))
def fix(sid,i,a,b_):
    s=next(x for x in SC if x['id']==sid); assert a in s['steps'][i],(sid,i,s['steps'][i]); s['steps'][i]=s['steps'][i].replace(a,b_)
# steps that named things this redesign does not have, and the M/A/R/C letters
fix('water',2,'Switch to your water ledger.','Switch to your stored water.')
fix('water',3,'See Learn → Make water safe.','See Learn, Make water safe to drink.')
fix('evac',2,'Use your saved routes.','Use the routes you planned.')
for i,l in enumerate('MARC'): fix('hurt',i,l+'. ','')
for s in SC:
    for st in s['steps']: assert '—' not in st and '→' not in st
def rep(a,b,n=1):
    global src
    assert src.count(a)==n,(a,src.count(a)); src=src.replace(a,b)
AUDIT=[
["Search","Every word you type has to appear letter for letter, inside any word. Out of 28 everyday questions, 9 do not show the right answer in the top 3. <b>generater</b> and <b>how much bleach per gallon</b> return nothing. <code>index.html</code> runSearch","New search: fixes typos, knows short names, matches whole words, drops filler words.","M"],
["Search ranking","99.8% of manual sections are titled “Page N”, so nearly every hit ties and they show in file order. An 1869 waterworks book is file 3 of 44. Where There Is No Doctor is file 41.","Rank by how well the text matches. Push old background books down. Never let the 1887 to 1918 canning books beat the 2015 USDA guide.","M"],
["Sidebar","All five tabs look the same: same weight, same one-color 16px symbol. Get maps, Offline check, Help and Theme are 12px footer text. <code>index.html:15-20, 44-50</code>","A color and drawn icon per tab, number keys, and a list of what is inside the open tab.","M"],
["Home, in an emergency","At the app's smallest window size the Something happening buttons drop below the setup and supplies cards. <code>ui.css:73</code> <code>Window.swift:25</code>","Emergency goes first, full width. An orange button for it sits in the sidebar on every screen.","M"],
["Home","Three search boxes across the app (sidebar, Home, My Place) and four cards that repeat the sidebar. <code>home.html:76</code> <code>place.html:116</code>","One search, in one place.","S"],
["Finding features","Search cannot find the calculators, drills, rescue card, radio log or Offline check. The rescue card is folded shut at the bottom of Home. <code>index.html:197-202</code> <code>home.html:117</code>","Add the app's own features to search and give the rescue card its own entry.","M"],
["Every situation","A red radiation banner moves to the top of every situation, so Power out opens with a radiation warning. <code>home.html:521</code>","Show it on the radiation situation only.","S"],
["Plan","A friend's copy says the plan is only in your edition. Checks are saved by position, so reordering steps moves checks onto the wrong steps. <code>index.html:138, 149</code>","Checklists anyone can create, with an ID per step.","M"],
["Backup","The app says “A backup is kept” but has no way to restore one. <code>place.html:214, 524</code>","One backup file with a preview before it restores.","M"],
["Map","With no map, the Get your state's map button is at the bottom of the side panel. Near me treats any pin with “home” in its name as Home, so a Home Depot pin counts. <code>map/index.html:360, 603</code>","Put the next step on the empty map. Use the Home record kind everywhere.","S"],
["Shortcuts","⌘K stops working after you click inside any screen. There is no Back or Forward key, no swipe and no zoom. <code>index.html:220</code> <code>Window.swift:103</code>","Every screen passes ⌘K up. Add ⌘[ and ⌘], swipe back, and zoom.","S"],
["Dark mode","The Delete button, error messages and the Offline check verdict put white text on light colors, about 2 to 1 contrast. <code>ui.css:79, 135</code>","Dark text on those colors.","S"],
["A friend's copy","Your own defaults leak in: plants filter to zone 8, the map falls back to Texas, guides say “household of 4” and “3 × 55 gal”. <code>plants.html:48</code> <code>guides.html:48, 64</code>","Neutral defaults, and the person's own numbers.","M"],
["The look","Three icon styles at once (emoji, symbols, typed marks), the same card for everything, and “Coming next” placeholders you cannot click. <code>og.js</code> <code>place.html:317</code>","One drawn icon set. Rows for secondary things. Remove the placeholders.","M"],
["Wording","Developer notes are shown to people: “Rebuild the library index”, “Run tools/packs/offgrid-pack”, raw 404 text. <code>learn.html:228</code> <code>map/index.html:606</code>","Plain actions a person can take.","S"],
["Learn","Links can open a file that is not on the Mac, which is a dead end in an emergency. “35 more titles can be added” is the second thing on the page. <code>learn.html:236, 420</code>","Hide what is not there. Move the add list to setup.","M"],
["Rescue card","Typed coordinates cannot be cleared, and the time in the radio script is frozen at the moment the card was drawn. <code>home.html:417, 454</code>","Clear on empty. Update the time on every read.","S"],
["Small windows","At the smallest window size My Place and Map leave about 312px for the actual content. <code>place.html:17</code> <code>map/index.html:14</code>","Fold the inner panels away below about 1000px.","M"],
["Screen readers","Tab symbols are read aloud, screens are announced as “place” and “home”, and Enter in search can open a result from the previous search. <code>index.html:44, 92, 219</code>","Hide the symbols, name the screens, wait for results before Enter acts.","S"]]
SR=[
["generater","Nothing. A typo returns zero results.","Fixes the typo and shows the generator, the Power out steps and the outage sheet."],
["co","5,968 hits. It matches cover, cold and cooking. Tornado warning comes first.","Only carbon monoxide results: the freeze steps that warn about it, your generator, and the outage sheet."],
["burn","384 tied results. An 1869 waterworks book is in the top 3 and the burn pages in Where There Is No Doctor are hidden.","Whole words only. The Burns page comes first."],
["battery","“A battery of nine boilers” from 1869 is third.","Your AA batteries and power station first."],
["no power","“No” matches not and now. The Power out steps drop out because they never say “no”.","Power out steps first."],
["how much bleach per gallon","Nothing. Even “how” and “much” must match.","Filler words are dropped. Bleach pages show."],
["frozen pipes","A home canning page.","Hard freeze steps and the winter storm sheet."],
["diarrhea kid","“Kid” matches kidneys in 12 of 12 results.","Kid means child. The Where There Is No Doctor page on diarrhea and the rehydration drink comes first."],
["purify water","An 1869 waterworks book.","Boil-water steps, then the bleach pages."]]
BUILD=[
["Swap the Kansas screenshot","S","Use a record with no pin. Check older releases for the same picture."],
["New sidebar, shortcuts and search","M","The change you will feel most. Color tabs, number keys, pop-up search with better ranking."],
["Home and Something happening","S","Emergency first, one search, the radiation banner only where it belongs."],
["Map and Get maps","M","A next step on the empty map, tools on demand, a drive as a normal choice."],
["Plan you can edit","M","Checklists in every copy. Checks stay with their step."],
["My Place and backup","M","One list, hidden coordinates, a backup you can actually restore."],
["Learn and wording","S","Hide what is not on the Mac. Plain words in place of developer notes."],
["Small windows and phone","M","Inner panels fold away. A bottom tab bar on the phone."]]
J=lambda o: json.dumps(o,ensure_ascii=False).replace('</','<\\/')
rep('__PASSAGES__',J(P)); rep('__SCEN__',J(SC)); rep('__AUDIT__',J(AUDIT)); rep('__SEARCHROWS__',J(SR)); rep('__BUILD__',J(BUILD))
open(S+'/fieldbook-redesign.html','w').write(src)
print(len(src))
