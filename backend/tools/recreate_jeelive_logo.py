import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageFilter

SOURCE = Path('/app/data/brand/jeelive-original-reference.jpg')
OUT = Path('/app/frontend/public/brand/jeelive-vector.svg')
WORK = SOURCE.parent
REGIONS = {'symbol': (95, 570, 500, 1135), 'wordmark': (545, 725, 1510, 935), 'tagline': (550, 950, 1510, 1045)}


def trace(image, name, bounds):
    gray = image.crop(bounds).convert('L').filter(ImageFilter.MedianFilter(3))
    mask = gray.point(lambda v: 0 if v < 195 else 255, mode='1')
    pbm = WORK / (name + '.pbm')
    svg = WORK / (name + '.svg')
    mask.save(pbm)
    subprocess.run(['potrace', str(pbm), '-s', '-o', str(svg), '--turdsize', '4', '--alphamax', '1', '--opttolerance', '0.15'], check=True)
    root = ET.parse(svg).getroot()
    group = root.find('{http://www.w3.org/2000/svg}g')
    group.set('fill', '#EF3445' if name == 'symbol' else '#FAF7F5' if name == 'wordmark' else '#FF6974')
    fragment = ET.tostring(group, encoding='unicode')
    fragment = re.sub(r'ns\d+:', '', fragment)
    fragment = re.sub(r' xmlns:ns\d+="[^"]+"', '', fragment)
    x, y = bounds[0] - 95, bounds[1] - 570
    return f'<g transform="translate({x} {y})">{fragment}</g>'


if __name__ == '__main__':
    image = Image.open(SOURCE).convert('RGB')
    if image.size != (1600, 1600):
        raise ValueError('Reference image dimensions changed')
    groups = ''.join(trace(image, name, bounds) for name, bounds in REGIONS.items())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1415 565" role="img" aria-labelledby="title"><title id="title">Jeelive.ai — SCORE 200+ WITH AI</title><defs><linearGradient id="emblem" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EAE3E3"/><stop offset="0.48" stop-color="#B81226"/><stop offset="1" stop-color="#E11C35"/></linearGradient></defs>' + groups + '</svg>')
    print('Vector logo generated', OUT.stat().st_size, 'bytes; no embedded bitmap or font dependency')
