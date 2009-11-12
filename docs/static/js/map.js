        var map, layer;
        function update_attribution(data) {
            map.layers[0].attribution = data['attribution'];
            map.events.triggerEvent("changelayer")
        }
        function call_update_attribution(map) {
            var s = document.createElement("script");
            s.src="http://openaerialmap.hypercube.telascience.org/attribution/?bbox="+map.getExtent().toBBOX()+"&scale="+map.getScale()+"&callback=update_attribution";
            document.body.appendChild(s);
        }
        function map_init(location, zoom){
            OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
            map = new OpenLayers.Map( 'map', { 
               maxResolution: 1.40625/2,
               numZoomLevels: 22, 
               controls: [  
                 new OpenLayers.Control.Scale(), 
                 new OpenLayers.Control.PanZoomBar(), 
                 new OpenLayers.Control.Permalink(), 
                 new OpenLayers.Control.Navigation(), 
                 new OpenLayers.Control.Attribution()
                ]
              } 
            );
            layer = new OpenLayers.Layer.WMS( "OpenStreetMap", 
             [
              "http://oam1.hypercube.telascience.org/tiles/",
              "http://oam2.hypercube.telascience.org/tiles/",
              "http://oam3.hypercube.telascience.org/tiles/"
             ],
                 {layers: 'openaerialmap'}, {'wrapDateLine': true, buffer: 1} );
            map.addLayer(layer);
            layer = new OpenLayers.Layer.WMS( "OpenStreetMap", 
             [
              "http://osm1.hypercube.telascience.org/tiles/",
              "http://osm2.hypercube.telascience.org/tiles/",
              "http://osm3.hypercube.telascience.org/tiles/"
             ],
                 {layers: 'osm-4326-hybrid'},
                 {'attribution':'<a href="http://openstreetmap.org/">OpenStreetMap</a>', isBaseLayer: false, visibility: false, buffer:1});
            map.addLayer(layer);
            if (!map.getCenter()) {
              if (location) { 
                map.setCenter(location, zoom); 
              } else {
                map.zoomToMaxExtent();
              }  
            }
            map.events.register("moveend", map, function() { call_update_attribution(this); });
            call_update_attribution(map);
        }
