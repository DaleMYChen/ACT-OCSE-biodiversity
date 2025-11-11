var L = window.L;

L.Control.SideBySide = L.Control.extend({
    options: {
        thumbSize: 42,
        padding: 0
    },

    initialize: function(leftLayer, rightLayer, options) {
        this.setLeftLayer(leftLayer);
        this.setRightLayer(rightLayer);
        L.setOptions(this, options);
    },

    getPosition: function() {
        var rangeValue = this._range.value;
        var offset = (0.5 - rangeValue) * (2 * this.options.padding + this.options.thumbSize);
        return this._map.getSize().x * rangeValue + offset;
    },

    setPosition: function(position) {
        var size = this._map.getSize();
        var value = (position - this.options.padding - this.options.thumbSize / 2) / (size.x - 2 * this.options.padding - this.options.thumbSize);
        this._range.value = value;
        this._updateLayers();
    },

    includes: L.Evented.prototype || L.Mixin.Events,

    addTo: function(map) {
        this.remove();
        this._map = map;

        var container = this._container = L.DomUtil.create('div', 'leaflet-sbs', map._controlContainer);

        this._divider = L.DomUtil.create('div', 'leaflet-sbs-divider', container);
        this._range = L.DomUtil.create('input', 'leaflet-sbs-range', container);
        this._range.type = 'range';
        this._range.min = 0;
        this._range.max = 1;
        this._range.step = 'any';
        this._range.value = 0.5;
        this._range.style.paddingLeft = this._range.style.paddingRight = this.options.padding + 'px';

        // Prevent map drag when using the slider
        L.DomEvent.on(this._range, 'mousedown', L.DomEvent.stopPropagation);
        L.DomEvent.on(this._range, 'touchstart', L.DomEvent.stopPropagation);
        L.DomEvent.on(container, 'mousedown', L.DomEvent.stopPropagation);
        L.DomEvent.on(container, 'touchstart', L.DomEvent.stopPropagation);
        
        this._addEvents();
        this._updateLayers();
        return this;
    },

    remove: function() {
        if (!this._map) {
            return this;
        }
        if (this._leftLayer) {
            this._leftLayer.getContainer().style.clip = '';
        }
        if (this._rightLayer) {
            this._rightLayer.getContainer().style.clip = '';
        }
        this._removeEvents();
        L.DomUtil.remove(this._container);

        this._map = null;

        return this;
    },

    setLeftLayer: function(layer) {
        this._leftLayer = layer;
        this._updateLayers();
        return this;
    },

    setRightLayer: function(layer) {
        this._rightLayer = layer;
        this._updateLayers();
        return this;
    },

    _updateClip: function() {
        var map = this._map;
        var nw = map.containerPointToLayerPoint([0, 0]);
        var se = map.containerPointToLayerPoint(map.getSize());
        var clipX = nw.x + this.getPosition();
        var dividerX = this.getPosition();

        this._divider.style.left = dividerX + 'px';
        this.fire('dividermove', {x: dividerX});

        var clipLeft = 'rect(' + [nw.y, clipX, se.y, nw.x].join('px,') + 'px)';
        var clipRight = 'rect(' + [nw.y, se.x, se.y, clipX].join('px,') + 'px)';

        if (this._leftLayer) {
            this._leftLayer.getContainer().style.clip = clipLeft;
        }
        if (this._rightLayer) {
            this._rightLayer.getContainer().style.clip = clipRight;
        }
    },

    _updateLayers: function() {
        if (!this._map) {
            return this;
        }
        this._updateClip();
        return this;
    },

    _addEvents: function() {
        var range = this._range;
        var map = this._map;
        if (!map || !range) return;

        map.on('move', this._updateLayers, this);
        map.on('layeradd layerremove', this._updateLayers, this);
        L.DomEvent.on(range, 'input', this._updateLayers, this);
        L.DomEvent.on(range, 'change', this._updateLayers, this);

        // Prevent map drag when interacting with the divider
        L.DomEvent.on(this._divider, 'mousedown', function(e) {
            L.DomEvent.stopPropagation(e);
            L.DomEvent.disableClickPropagation(this._range);
        }, this);
    },

    _removeEvents: function() {
        var range = this._range;
        var map = this._map;
        if (range) {
            L.DomEvent.off(range, 'input', this._updateLayers, this);
            L.DomEvent.off(range, 'change', this._updateLayers, this);
        }
        if (map) {
            map.off('layeradd layerremove', this._updateLayers, this);
            map.off('move', this._updateLayers, this);
        }
    }
});

L.control.sideBySide = function(leftLayer, rightLayer, options) {
    return new L.Control.SideBySide(leftLayer, rightLayer, options);
};