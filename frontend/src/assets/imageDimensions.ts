/** Header-only layout hint. Never transform/recompress the supplied source. */
export function imageDimensions(b: Uint8Array): { width?: number; height?: number } {
  const v = new DataView(b.buffer, b.byteOffset, b.byteLength);
  const valid = (width: number, height: number) => width > 0 && height > 0 && width <= 100000 && height <= 100000 ? { width, height } : {};
  try {
    if (b.length >= 24 && v.getUint32(0) === 0x89504e47 && v.getUint32(4) === 0x0d0a1a0a) return valid(v.getUint32(16), v.getUint32(20));
    if (b.length >= 10 && b[0] === 71 && b[1] === 73 && b[2] === 70) return valid(v.getUint16(6, true), v.getUint16(8, true));
    if (b.length >= 30 && v.getUint32(0) === 0x52494646 && v.getUint32(8) === 0x57454250) {
      if (v.getUint32(12) === 0x56503858) return valid(1 + b[24] + (b[25] << 8) + (b[26] << 16), 1 + b[27] + (b[28] << 8) + (b[29] << 16));
      if (v.getUint32(12) === 0x56503820 && b[23] === 0x9d && b[24] === 1 && b[25] === 0x2a) return valid(v.getUint16(26, true) & 0x3fff, v.getUint16(28, true) & 0x3fff);
      if (v.getUint32(12) === 0x5650384c && b[20] === 0x2f) return valid(1 + b[21] + ((b[22] & 63) << 8), 1 + (b[22] >> 6) + (b[23] << 2) + ((b[24] & 15) << 10));
    }
    if (b[0] === 0xff && b[1] === 0xd8) {
      for (let i = 2; i + 8 < b.length;) {
        if (b[i++] !== 0xff) break;
        while (b[i] === 0xff) i++;
        const marker = b[i++];
        if (marker === 0xda || marker === 0xd9) break;
        const length = v.getUint16(i);
        if ([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf].includes(marker)) return valid(v.getUint16(i + 5), v.getUint16(i + 3));
        if (length < 2) break;
        i += length;
      }
    }
  } catch { /* Unknown/corrupt format: decoder remains the authority. */ }
  return {};
}