"""Keep only new image-generated pigment on an otherwise exact ancestral wall."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

BASE = Path('artifacts/line-1/wall.png')
OUT = Path('artifacts/line-1/wall-v11.png')
ANCESTOR = '74973235129c9342d75f1354bfae1265c1f8f4e7507e9a963ea6c95f595d5ec7'


def main():
    original = BASE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == ANCESTOR
    w, h, old = read_png(original)
    draft = OUT.read_bytes()
    gw, gh, generated = read_png(draft)
    assert (w, h) == (gw, gh) == (1254, 1254)
    final = bytearray(old)
    changed, bounds = 0, [w, h, 0, 0]
    # Vacant stone left of the ancestor's knee. Keep all ancestral paint outside
    # this ellipse exact; preserve stone relief even within the new pigment.
    for y in range(768, 868):
        for x in range(287, 410):
            if ((x-348)/60)**2 + ((y-817)/49)**2 > 1:
                continue
            i = (y*w+x)*3
            r, g, b = generated[i:i+3]
            rock = old[i:i+3]
            if max(rock) < 65:
                continue
            if r < 95 and g < 80 and b < 65:
                pigment, alpha = (45, 31, 23), .55
            elif r > g*1.35 and r > b*1.65 and r > 90:
                pigment, alpha = (142, 65, 29), .45
            else:
                continue
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha)+pigment[c]*alpha)
            if final[i:i+3] != old[i:i+3]:
                changed += 1
                bounds = [min(bounds[0], x), min(bounds[1], y),
                          max(bounds[2], x), max(bounds[3], y)]
    assert changed > 1000
    encoded = png(w, h, final)
    BASE.write_bytes(encoded)
    OUT.write_bytes(encoded)
    thumb = jpeg(512, 512, resize(w, h, final), 52)
    assert len(thumb) < 100000
    Path('dist/line-1/31.jpg').write_bytes(thumb)
    wall_hash = hashlib.sha256(encoded).hexdigest()
    record = {
        'name': 'The Kept Stone',
        'image': 'https://api.imd.fun/artifacts/'+wall_hash,
        'attributes': [
            {'trait_type': 'Cave', 'value': 'Water'},
            {'trait_type': 'Wall', 'value': 'Line 1'},
            {'trait_type': 'Number', 'value': 31},
            {'trait_type': 'Left behind', 'value': 'Retained snapshot pin'},
            {'trait_type': 'Meaning', 'value': 'A bound ochre stone beside Pepe remembers the separate reference that detects a replaced observation.'},
            {'trait_type': 'One thing', 'value': 'portable live Ethereum JSON-RPC snapshots'}
        ]
    }
    Path('dist/line-1/31.json').write_text(json.dumps(record, indent=2)+'\n')
    review = {
        'record': 31, 'ancestor_sha256': ANCESTOR,
        'output_sha256': wall_hash,
        'wall': {'paths': [str(BASE), str(OUT)], 'format': 'PNG',
                 'width': w, 'height': h, 'mode': 'RGB'},
        'thumbnail': {'path': 'dist/line-1/31.jpg', 'format': 'JPEG',
                      'width': 512, 'height': 512, 'bytes': len(thumb)},
        'generation': {'tool': 'image_gen.imagegen',
                       'draft_sha256': hashlib.sha256(draft).hexdigest(),
                       'draft_retained': False},
        'preservation': 'All pixels outside the new small ellipse are exactly ancestral; only generated charcoal/ochre pigment was blended with original rock relief inside it.',
        'changed_pixels': changed, 'unchanged_pixels': w*h-changed,
        'changed_bounds_inclusive': bounds,
        'visual_review': 'Pending final inspection',
        'unmet_visual_requirements': []
    }
    Path('line-1/wall-review-31.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
