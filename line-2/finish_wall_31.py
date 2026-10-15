"""Transfer only new generated pigment onto unpainted ancestral stone."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

base = Path('artifacts/line-2/wall.png')
target = Path('artifacts/line-2/wall-v11.png')
ancestor = base.read_bytes()
assert hashlib.sha256(ancestor).hexdigest() == 'ec3417d93687bf199ef6c2391fdd7d7db93393b9306d5bf01647700dec5e737d'
w, h, old = read_png(ancestor)
draft = target.read_bytes()
dw, dh, generated = read_png(draft)
assert (w,h) == (1254,1254)
# Normalized crop covers the complete generated motif, including its outer oval.
cx, cy, cw, ch = [round(v) for v in (dw*.195, dh*.045, dw*.59, dh*.85)]
x0, y0, width, height = 1035, 770, 170, 195
final = bytearray(old)
changed = 0
for y in range(y0,y0+height):
    for x in range(x0,x0+width):
        i = (y*w+x)*3
        rock = old[i:i+3]
        sx = cx + (x-x0)*cw//width
        sy = cy + (y-y0)*ch//height
        j = (sy*dw+sx)*3
        r,g,b = generated[j:j+3]
        if max(rock) < 85 or (x*19+y*31)%19 == 0:
            continue
        charcoal = max(r,g,b) < 110 and sum(rock)-r-g-b > 60
        ochre = r > 65 and g < r*.57 and b < r*.40 and rock[1]-g > 20
        if charcoal or ochre:
            pigment = (48,33,21) if charcoal else (139,54,24)
            alpha = .72 if charcoal else .66
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha)+pigment[c]*alpha)
            changed += 1
assert 500 < changed < width*height
for y in range(h):
    for x in range(w):
        i=(y*w+x)*3
        if final[i:i+3] != old[i:i+3]:
            assert x0<=x<x0+width and y0<=y<y0+height
            assert max(old[i:i+3])>=85
encoded=png(w,h,final)
base.write_bytes(encoded)
target.write_bytes(encoded)
preview=jpeg(512,512,resize(w,h,final),52)
assert len(preview)<=100000
Path('dist/line-2/31.jpg').write_bytes(preview)
review={'number':31,'ancestor_sha256':hashlib.sha256(ancestor).hexdigest(),
         'sha256':hashlib.sha256(encoded).hexdigest(),
         'wall':{'paths':[str(base),str(target)],'width':w,'height':h,'format':'PNG','mode':'RGB'},
         'preview':{'path':'dist/line-2/31.jpg','width':512,'height':512,'format':'JPEG','bytes':len(preview)},
         'addition_region':{'x':x0,'y':y0,'width':width,'height':height},
         'changed_pixels':changed,'unchanged_pixels':w*h-changed,
         'outside_region_pixel_identical':True,'dark_cracks_preserved':True,
         'generation_tool':'mcp__image__generate_image','draft_sha256':hashlib.sha256(draft).hexdigest(),
         'generated_dimensions':[dw,dh],'draft_retained':False,
         'visual_review':'pending inspection','unmet_visual_requirements':[]}
Path('line-2/wall-review-31.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(review,indent=2))
