const initOpenStreetMap = () => {
  const mapShell = document.querySelector('#mapPage .google-map');
  const points = window.FISHON_BUSAN_POINTS || [];
  if (!mapShell || !window.L || mapShell.dataset.mapReady) return;
  mapShell.dataset.mapReady = 'true';
  mapShell.innerHTML = '<div id="fishonOsmMap" aria-label="부산 낚시 포인트 지도"></div><div class="osm-map-label">피쉬온 포인트 DB · OpenStreetMap</div>';

  const map = window.L.map('fishonOsmMap', { zoomControl: false, attributionControl: true }).setView([35.1796, 129.0756], 10);
  window.L.control.zoom({ position: 'bottomright' }).addTo(map);
  window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  points.forEach(point => {
    const marker = window.L.circleMarker([point.latitude, point.longitude], { radius: 8, color: '#ffffff', weight: 2, fillColor: '#087d86', fillOpacity: 1 }).addTo(map);
    marker.bindPopup(`<b>${point.name}</b><br><small>${point.district} · ${point.species.join(' · ')}<br>${point.status}</small><br><a href="https://www.openstreetmap.org/?mlat=${point.latitude}&mlon=${point.longitude}#map=15/${point.latitude}/${point.longitude}" target="_blank" rel="noopener">위치 보기 ↗</a>`);
  });

  document.querySelectorAll('[data-go="map"]').forEach(button => button.addEventListener('click', () => setTimeout(() => map.invalidateSize(), 80)));
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initOpenStreetMap);
} else {
  initOpenStreetMap();
}
