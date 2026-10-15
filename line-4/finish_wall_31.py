"""One-time preservation pass retaining only generated pigment on vacant stone."""
import hashlib
import json
from pathlib import Path

from image_bytes import jpeg, png, read_png, resize


def main():
    folder = Path('artifacts/line-4')
    ancestor = (folder / 'wall.png').read_bytes()
    generated = (folder / 'wall-v11.png').read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == '588133156ee1205142e99d24990d6db5f3a15658a3b9c5c6c687145b642e9cb5'
    assert hashlib.sha256(generated).hexdigest() == 'f6f307064633cd2fd9a58206967f3e757771b7a32dc001647e6e73cdf4e91cc2'
    w, h, old = read_png(ancestor)
    gw, gh, draft = read_png(generated)
    assert (w, h, gw, gh) == (1254, 1254, 1254, 1254)
    final = bytearray(old)
    changed = 0
    for y in range(155, 257):
        for x in range(248, 415):
            i = (y * w + x) * 3
            r, g, b = draft[i:i+3]
            charcoal = r < 112 and g < 87 and b < 65 and r-g < 36
            pebble = ((x-278)**2 + (y-235)**2 < 18**2 or
                      (x-369)**2 + (y-240)**2 < 17**2)
            ochre = pebble and r > g*1.35 and r-g > 40
            original = old[i:i+3]
            if not (charcoal or ochre) or sum(original) < 160:
                continue
            # Pigment is derived from the image-tool draft; retain the original
            # rock's relief by applying its original luminance to that pigment.
            target = ([v*.34 for v in original] if charcoal else
                      [original[0]*.86, original[1]*.49, original[2]*.36])
            final[i:i+3] = bytes(round(v*.15+t*.85) for v, t in zip(original, target))
            changed += final[i:i+3] != original
    assert 1000 < changed < 12000
    for i in range(0, len(old), 3):
        if old[i:i+3] != final[i:i+3]:
            y, x = divmod(i//3, w)
            assert 248 <= x < 415 and 155 <= y < 257
            assert sum(old[i:i+3]) >= 160
    wall = png(w, h, final)
    sha = hashlib.sha256(wall).hexdigest()
    preview = jpeg(512, 512, resize(w, h, final), 52)
    assert len(preview) < 100_000
    for name in ('wall.png', 'wall-v11.png'):
        (folder/name).write_bytes(wall)
    Path('dist/line-4/31.jpg').write_bytes(preview)
    review = {
        'wall': {'paths': ['artifacts/line-4/wall.png', 'artifacts/line-4/wall-v11.png'],
                 'width': w, 'height': h, 'format': 'PNG', 'mode': 'RGB',
                 'bytes': len(wall), 'sha256': sha},
        'preview': {'path': 'dist/line-4/31.jpg', 'width': 512, 'height': 512,
                    'format': 'JPEG', 'bytes': len(preview),
                    'sha256': hashlib.sha256(preview).hexdigest()},
        'ancestorSha256': hashlib.sha256(ancestor).hexdigest(),
        'generatedDraftSha256': hashlib.sha256(generated).hexdigest(),
        'imageTool': 'Installed image edit adapter, request 25dbc735-96ad-4a41-aa79-279446bb8904',
        'prompt': 'Preserve inherited 1254-square cave wall and all ancestor paintings; add only a small worn charcoal balance with two uneven ochre pebbles and a tiny flake on vacant upper-left stone. Earth pigments, no text or new hands; preserve both inherited five-digit hands.',
        'changedPixels': changed, 'unchangedPixels': w*h-changed,
        'additionBoundsExclusive': [248, 155, 415, 257],
        'preservation': 'Every pixel outside the vacant-stone addition and every deep fissure pixel inside is identical to the hash-verified ancestor. Pepe, hands, all ancestral pigment and framing are outside the addition.',
        'visualReview': 'Pending final inspection.',
        'unmetVisualRequirements': [],
        'limitations': ['Local inspection and byte checks are not independent visual certification.',
                        'Small worn balance is subtle at thumbnail scale.',
                        'Only generated pigment was retained; the full image-tool draft changed rock texture.'],
    }
    Path('line-4/wall-review-31.json').write_text(json.dumps(review, indent=2)+'\n')
    record = {
        'name': 'The Weight of a Flake',
        'image': 'https://api.imd.fun/artifacts/'+sha,
        'attributes': [
            {'trait_type': 'Cave', 'value': 'Water'},
            {'trait_type': 'Wall', 'value': 'Line 4'},
            {'trait_type': 'Number', 'value': 31},
            {'trait_type': 'Left behind', 'value': 'offline EIP-712 integer reviewer'},
            {'trait_type': 'Meaning', 'value': 'Pepe weighs two pebbles and notices the small flake that rounding would lose.'},
            {'trait_type': 'One thing', 'value': 'offline EIP-712 typed-data digest checking'},
        ],
    }
    Path('dist/line-4/31.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
