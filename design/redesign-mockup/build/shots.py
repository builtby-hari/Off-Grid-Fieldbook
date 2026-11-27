import sys
S=sys.argv[1]; t=open(S+'/fieldbook-redesign.html').read()
head='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
open(S+'/pack/Fieldbook-redesign-pack/Fieldbook-redesign.html','w').write(head+t+'</body></html>')
shots={'01-home':'','02-search':'go("home");openPal("generater co");noteKey="search";drawNotes();','03-something-happening':'go("emergency:power");','04-map':'go("map:layers");','04b-map-coordinates':'S.showll=true;go("map:near");','05-map-no-map-yet':'S.mapEmpty=true;go("map");','06-get-maps':'S.setup.state="Texas";go("setup");','07-my-place':'go("place:barrel");','07b-my-place-coordinates':'S.showll=true;go("place:meet");','08-supplies-sheet':'go("supplies");','09-supplies-add-bar':'S.supq="ba";go("supplies");','10-sun-and-time':'go("sun");','10b-sun-year-and-calendar':'go("sun");SCROLL=800;','11-learn':'go("learn");','12-learn-manual-page':'go("learn:read:m19");','13-living-with-the-land':'go("earth");','13b-living-with-the-land-ideas':'go("earth");SCROLL=420;','14-plan-checklist':'go("plan:p-power");','15-plan-family-card':'go("plan:p-family");','16-readiness-check':'go("check");'}
jobs=[]; tail='render();\n</script>'; assert t.count(tail)==1
def make(name,js,dark=False,phone=False):
    extra='var SCROLL=0;'+js+'document.documentElement.dataset.theme="%s";'%('dark' if dark else 'light')+('S.device="phone";document.getElementById("appwrap").classList.add("phone");render(true);' if phone else '')+'drawMap();document.getElementById("view").scrollTop=SCROLL;'
    open(S+'/pack/tmp/'+name+'.html','w').write(head+t.replace(tail,'render();\n'+extra+'\n</script>')+'</body></html>'); jobs.append(name)
for k,v in shots.items(): make(k+'-mac-light',v)
for k in ['01-home','02-search','03-something-happening','08-supplies-sheet','10-sun-and-time','11-learn','13-living-with-the-land','14-plan-checklist']: make(k+'-mac-dark',shots[k],dark=True)
for k in ['01-home','03-something-happening','04-map','08-supplies-sheet','10-sun-and-time','14-plan-checklist']: make(k+'-phone-light',shots[k],phone=True)
open(S+'/pack/jobs.txt','w').write('\n'.join(jobs)+'\n')
