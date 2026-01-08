import { ColorScale } from '@microsoft/fast-colors';

const PATCH_MARKER = '__mercurySafeSort';

function compareStops(left, right) {
  const a = left.position;
  const b = right.position;
  if (a < b) {
    return -1;
  }
  if (a > b) {
    return 1;
  }
  return 0;
}

function safeSortColorScaleStops(stops) {
  if (!stops || typeof stops.length !== 'number') {
    return stops;
  }
  const list = Array.prototype.slice.call(stops);
  for (let i = 1; i < list.length; i++) {
    const item = list[i];
    let j = i - 1;
    while (j >= 0 && compareStops(list[j], item) > 0) {
      list[j + 1] = list[j];
      j -= 1;
    }
    list[j + 1] = item;
  }
  return list;
}

if (!ColorScale.prototype.sortColorScaleStops[PATCH_MARKER]) {
  // Workaround for FAST color-scale recursion (see microsoft/fast#7057).
  ColorScale.prototype.sortColorScaleStops = function (stops) {
    return safeSortColorScaleStops(stops);
  };
  ColorScale.prototype.sortColorScaleStops[PATCH_MARKER] = true;
}
