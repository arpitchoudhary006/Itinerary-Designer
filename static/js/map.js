/**
 * Himalayan Itinerary Designer - Leaflet Map Integration
 * Supports Topographic & Street layers, custom pins for Destination, Hotels, Homestays, Activities,
 * and dynamic category filtering.
 */

window.HimalayanMap = (function () {
    // Custom SVG Pin Generator
    function createCustomIcon(bgColor, symbol) {
        return L.divIcon({
            className: 'custom-leaflet-marker',
            html: `
                <div style="
                    background: ${bgColor};
                    width: 34px;
                    height: 34px;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                    border: 2px solid #ffffff;
                ">
                    <span style="transform: rotate(45deg); font-size: 16px; line-height: 1;">${symbol}</span>
                </div>
            `,
            iconSize: [34, 34],
            iconAnchor: [17, 34],
            popupAnchor: [0, -34]
        });
    }

    const ICONS = {
        destination: createCustomIcon('#d97706', '🏔️'),
        hotel: createCustomIcon('#059669', '🏨'),
        homestay: createCustomIcon('#7c3aed', '🏡'),
        camp: createCustomIcon('#ea580c', '⛺'),
        activity: createCustomIcon('#0284c7', '🚩')
    };

    function initDestinationMap(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container || !window.L) return null;

        const centerLat = data.destination.latitude;
        const centerLng = data.destination.longitude;

        if (!centerLat || !centerLng) {
            container.innerHTML = '<div style="padding:40px; text-align:center; color:#64748b;">GPS Coordinates unavailable for this location.</div>';
            return null;
        }

        // Base tile layers
        const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '&copy; OpenStreetMap contributors'
        });

        const topoLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            maxZoom: 17,
            attribution: '&copy; OpenTopoMap contributors'
        });

        const map = L.map(containerId, {
            center: [centerLat, centerLng],
            zoom: 12,
            layers: [streetLayer]
        });

        // Layer Switcher
        const baseMaps = {
            "Street Map": streetLayer,
            "Topographic Terrain": topoLayer
        };
        L.control.layers(baseMaps, null, { position: 'topright' }).addTo(map);

        const markersGroup = {
            destination: L.layerGroup().addTo(map),
            hotel: L.layerGroup().addTo(map),
            homestay: L.layerGroup().addTo(map),
            activity: L.layerGroup().addTo(map)
        };

        const allLatLngs = [];

        // 1. Add Destination Main Marker
        const destMarker = L.marker([centerLat, centerLng], { icon: ICONS.destination })
            .bindPopup(`
                <div class="popup-hotel-card">
                    <h4>🏔️ ${data.destination.name}</h4>
                    <p style="font-size:0.85rem; color:#64748b; margin:4px 0;">${data.destination.state || 'Himalayas'} • Elevation: ${data.destination.elevation || 'High Altitude'}</p>
                    <p style="font-size:0.85rem;"><strong>Difficulty:</strong> ${data.destination.difficulty || 'Moderate'}</p>
                </div>
            `);
        markersGroup.destination.addLayer(destMarker);
        allLatLngs.push([centerLat, centerLng]);

        // 2. Add Accommodations (Hotels, Homestays, Camps)
        if (data.accommodations && Array.isArray(data.accommodations)) {
            data.accommodations.forEach(acc => {
                if (acc.latitude && acc.longitude) {
                    const accType = (acc.type || '').toLowerCase();
                    const iconKey = accType.includes('home') ? 'homestay' : (accType.includes('camp') ? 'camp' : 'hotel');
                    const groupKey = accType.includes('home') ? 'homestay' : 'hotel';

                    const popupHtml = `
                        <div class="popup-hotel-card">
                            ${acc.image_url ? `<img src="${acc.image_url}" alt="${acc.name}">` : ''}
                            <span class="tag ${iconKey}" style="font-size:0.7rem; margin-bottom:4px;">${acc.type}</span>
                            <h4>${acc.name}</h4>
                            <div class="popup-rating">⭐ ${acc.rating} (${acc.reviews_count || 0} reviews)</div>
                            <div class="popup-price">₹${Number(acc.price_per_night).toLocaleString('en-IN')} <span style="font-size:0.75rem; font-weight:normal; color:#64748b;">/ night</span></div>
                            <div style="font-size:0.8rem; color:#64748b; margin:4px 0;">📍 ${acc.distance || ''}</div>
                            ${acc.phone ? `<div style="font-size:0.8rem; margin-top:6px;"><a href="tel:${acc.phone}" class="btn sm primary" style="width:100%; text-align:center;">📞 Call ${acc.phone}</a></div>` : ''}
                        </div>
                    `;

                    const m = L.marker([acc.latitude, acc.longitude], { icon: ICONS[iconKey] || ICONS.hotel })
                        .bindPopup(popupHtml);
                    markersGroup[groupKey].addLayer(m);
                    allLatLngs.push([acc.latitude, acc.longitude]);
                }
            });
        }

        // 3. Add Activities
        if (data.activities && Array.isArray(data.activities)) {
            data.activities.forEach(act => {
                if (act.latitude && act.longitude) {
                    const m = L.marker([act.latitude, act.longitude], { icon: ICONS.activity })
                        .bindPopup(`
                            <div class="popup-hotel-card">
                                <h4>🚩 ${act.name}</h4>
                                <p style="font-size:0.85rem; color:#64748b;">${act.description || ''}</p>
                                <div style="font-size:0.85rem; font-weight:700; margin-top:4px;">Duration: ${act.duration || 'Flexible'} • ₹${Number(act.estimated_cost || 0).toLocaleString('en-IN')}</div>
                            </div>
                        `);
                    markersGroup.activity.addLayer(m);
                    allLatLngs.push([act.latitude, act.longitude]);
                }
            });
        }

        // Fit map bounds to show all pins comfortably
        if (allLatLngs.length > 1) {
            map.fitBounds(allLatLngs, { padding: [40, 40] });
        }

        // Connect filter buttons
        document.querySelectorAll('.map-filter-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.map-filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                const filter = this.dataset.filter;

                if (filter === 'all') {
                    map.addLayer(markersGroup.destination);
                    map.addLayer(markersGroup.hotel);
                    map.addLayer(markersGroup.homestay);
                    map.addLayer(markersGroup.activity);
                } else if (filter === 'hotels') {
                    map.removeLayer(markersGroup.activity);
                    map.removeLayer(markersGroup.homestay);
                    map.addLayer(markersGroup.hotel);
                    map.addLayer(markersGroup.destination);
                } else if (filter === 'homestays') {
                    map.removeLayer(markersGroup.activity);
                    map.removeLayer(markersGroup.hotel);
                    map.addLayer(markersGroup.homestay);
                    map.addLayer(markersGroup.destination);
                } else if (filter === 'activities') {
                    map.removeLayer(markersGroup.hotel);
                    map.removeLayer(markersGroup.homestay);
                    map.addLayer(markersGroup.activity);
                    map.addLayer(markersGroup.destination);
                }
            });
        });

        return map;
    }

    // Himalayan Explorer Map (All Destinations)
    function initExplorerMap(containerId, destinations) {
        const container = document.getElementById(containerId);
        if (!container || !window.L || !destinations || !destinations.length) return null;

        const map = L.map(containerId, {
            center: [31.1048, 77.1734], // Center of Himachal/Uttarakhand Himalayas
            zoom: 7
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        const bounds = [];

        destinations.forEach(dest => {
            if (dest.latitude && dest.longitude) {
                const marker = L.marker([dest.latitude, dest.longitude], { icon: ICONS.destination })
                    .bindPopup(`
                        <div class="popup-hotel-card">
                            ${dest.image_url ? `<img src="${dest.image_url}" alt="${dest.name}">` : ''}
                            <span class="tag" style="margin-bottom:4px;">${dest.state || 'Himalayas'}</span>
                            <h4>${dest.name}</h4>
                            <p style="font-size:0.85rem; color:#64748b; margin:4px 0;">${dest.description ? dest.description.substring(0, 95) + '...' : ''}</p>
                            <div style="font-size:0.85rem; font-weight:700; margin-bottom:8px;">Typical stay: ${dest.duration || 'Flexible'} • ${dest.difficulty || 'Moderate'}</div>
                            <a href="/destinations/${dest.slug}" class="btn sm primary" style="display:block; text-align:center;">Explore Guide & Stays →</a>
                        </div>
                    `);
                marker.addTo(map);
                bounds.push([dest.latitude, dest.longitude]);
            }
        });

        if (bounds.length) {
            map.fitBounds(bounds, { padding: [40, 40] });
        }

        return map;
    }

    return {
        initDestinationMap: initDestinationMap,
        initExplorerMap: initExplorerMap
    };
})();
