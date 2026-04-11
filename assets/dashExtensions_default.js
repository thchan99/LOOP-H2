window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng) {
                const c = feature.properties.color || "black";
                const ico = feature.properties.icon || "fa-circle";
                const html = `<i class="fa-solid ${ico}" style="color:${c}; font-size:22px;"></i>`;
                const icon = L.divIcon({
                    html: html,
                    className: "",
                    iconSize: [22, 22],
                    iconAnchor: [11, 11]
                });
                return L.marker(latlng, {
                    icon: icon
                });
            }

            ,
        function1: function(feature, layer) {
            if (feature.properties && feature.properties.popup) {
                layer.bindPopup(feature.properties.popup);
            }
        }

    }
});