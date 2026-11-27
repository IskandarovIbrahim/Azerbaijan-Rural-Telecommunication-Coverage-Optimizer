"use strict";

function createMapCamera(viewport, layer, onScaleChange) {
  const minimum = 1;
  const maximum = 5;
  const step = 1.4;
  const controls = viewport.querySelector(".map-tools");
  const zoomIn = controls.querySelector('[data-camera="in"]');
  const zoomOut = controls.querySelector('[data-camera="out"]');
  const resetButton = controls.querySelector('[data-camera="reset"]');
  const zoomLabel = controls.querySelector(".map-zoom-level");
  const pointers = new Map();

  let scale = minimum;
  let offsetX = 0;
  let offsetY = 0;
  let dragging = false;
  let suppressClick = false;

  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const center = () => [viewport.clientWidth / 2, viewport.clientHeight / 2];

  function coordinates(event) {
    const bounds = viewport.getBoundingClientRect();
    return [event.clientX - bounds.left, event.clientY - bounds.top];
  }

  function refresh() {
    offsetX = clamp(offsetX, viewport.clientWidth * (1 - scale), 0);
    offsetY = clamp(offsetY, viewport.clientHeight * (1 - scale), 0);
    layer.style.transform = "translate(" + offsetX + "px, " + offsetY + "px) scale(" + scale + ")";
    layer.style.setProperty("--map-icon-scale", 1 / scale);
    viewport.classList.toggle("can-pan", scale > minimum);
    zoomIn.disabled = scale >= maximum;
    zoomOut.disabled = scale <= minimum;
    resetButton.disabled = scale === minimum;
    zoomLabel.textContent = Math.round(scale * 100) + "%";
  }

  function zoomAt(value, from, to = from) {
    const next = clamp(value, minimum, maximum);
    const changed = next !== scale;
    const ratio = next / scale;
    offsetX = to[0] - (from[0] - offsetX) * ratio;
    offsetY = to[1] - (from[1] - offsetY) * ratio;
    scale = next;
    refresh();
    if (changed) onScaleChange();
  }

  function panBy(x, y) {
    offsetX += x;
    offsetY += y;
    refresh();
  }

  function reset() {
    zoomAt(minimum, center());
  }

  function startDrag() {
    dragging = true;
    suppressClick = true;
    viewport.classList.add("is-panning");
    for (const id of pointers.keys()) {
      if (!viewport.hasPointerCapture(id)) viewport.setPointerCapture(id);
    }
  }

  viewport.addEventListener("pointerdown", event => {
    if (event.button !== 0 || controls.contains(event.target) || pointers.size >= 2) return;
    if (!pointers.size) suppressClick = false;
    pointers.set(event.pointerId, coordinates(event));
    if (pointers.size === 2) startDrag();
  });

  viewport.addEventListener("pointermove", event => {
    const previous = pointers.get(event.pointerId);
    if (!previous) return;
    const point = coordinates(event);
    if (pointers.size === 2) {
      const other = [...pointers.entries()].find(([id]) => id !== event.pointerId)[1];
      const previousDistance = Math.hypot(previous[0] - other[0], previous[1] - other[1]);
      const distance = Math.hypot(point[0] - other[0], point[1] - other[1]);
      if (previousDistance > 0 && distance > 0) {
        const from = [(previous[0] + other[0]) / 2, (previous[1] + other[1]) / 2];
        const to = [(point[0] + other[0]) / 2, (point[1] + other[1]) / 2];
        zoomAt(scale * distance / previousDistance, from, to);
      }
    } else {
      const dx = point[0] - previous[0];
      const dy = point[1] - previous[1];
      if (!dragging) {
        if (scale === minimum || Math.hypot(dx, dy) < 4) return;
        startDrag();
      }
      panBy(dx, dy);
    }
    pointers.set(event.pointerId, point);
  });

  function releasePointer(event) {
    pointers.delete(event.pointerId);
    if (!pointers.size) {
      dragging = false;
      viewport.classList.remove("is-panning");
    }
  }

  for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) {
    viewport.addEventListener(type, releasePointer);
  }
  viewport.addEventListener("pointerleave", event => {
    if (!viewport.hasPointerCapture(event.pointerId)) releasePointer(event);
  });
  viewport.addEventListener("click", event => {
    if (suppressClick && event.detail > 0 && !controls.contains(event.target)) {
      event.preventDefault();
      event.stopPropagation();
      suppressClick = false;
    }
  }, true);

  viewport.addEventListener("wheel", event => {
    if (!event.ctrlKey) return;
    event.preventDefault();
    const units = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? viewport.clientHeight : 1;
    zoomAt(scale * Math.exp(-event.deltaY * units * .002), coordinates(event));
  }, {passive: false});

  const keyboard = {
    "+": () => zoomAt(scale * step, center()),
    "=": () => zoomAt(scale * step, center()),
    "-": () => zoomAt(scale / step, center()),
    "0": reset,
    ArrowLeft: () => panBy(45, 0),
    ArrowRight: () => panBy(-45, 0),
    ArrowUp: () => panBy(0, 45),
    ArrowDown: () => panBy(0, -45),
  };
  viewport.addEventListener("keydown", event => {
    if (event.target !== viewport || !Object.hasOwn(keyboard, event.key)) return;
    if (event.key.startsWith("Arrow") && scale === minimum) return;
    event.preventDefault();
    keyboard[event.key]();
  });
  zoomIn.addEventListener("click", () => zoomAt(scale * step, center()));
  zoomOut.addEventListener("click", () => zoomAt(scale / step, center()));
  resetButton.addEventListener("click", reset);
  refresh();
  return {reset, resize: refresh, get scale() { return scale; }};
}
