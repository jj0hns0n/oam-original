/* Copyright (c) 2006-2007 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */

/**
 * @requires OpenLayers/Control.js
 * 
 * Class: OpenLayers.Control.Panel
 *
 * Inherits from:
 *  - <OpenLayers.Control>
 */
OpenLayers.Control.Panel = OpenLayers.Class(OpenLayers.Control, {
    /**
     * Property: controls
     * Array({<OpenLayers.Control>})
     */
    controls: null,    
    
    /** 
     * APIProperty: defaultControl
     * <OpenLayers.Control> The control which is activated when the control is
     * activated (turned on), which also happens at instantiation.
     */
    defaultControl: null, 

    /**
     * Constructor: OpenLayers.Control 
     * 
     * Parameters:
     * options - {Object} An optional object whose properties will be used
     *     to extend the control.
     */
    initialize: function(options) {
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        this.controls = [];
    },

    /**
     * APIMethod: destroy
     */
    destroy: function() {
        OpenLayers.Control.prototype.destroy.apply(this, arguments);
        for(var i = this.controls.length - 1 ; i >= 0; i--) {
            OpenLayers.Event.stopObservingElement(this.controls[i].panel_div);
            this.controls[i].panel_div = null;
        }    
    },

    /**
     * APIMethod: activate
     */
    activate: function() {
        if (OpenLayers.Control.prototype.activate.apply(this, arguments)) {
            for(var i = 0; i < this.controls.length; i++) {
                if (this.controls[i] == this.defaultControl) {
                    this.controls[i].activate();
                }
            }    
            this.redraw();
            return true;
        } else {
            return false;
        }
    },
    
    /**
     * APIMethod: deactivate
     */
    deactivate: function() {
        if (OpenLayers.Control.prototype.deactivate.apply(this, arguments)) {
            for(var i = 0; i < this.controls.length; i++) {
                this.controls[i].deactivate();
            }    
            this.redraw();
            return true;
        } else {
            return false;
        }
    },
    
    /**
     * Method: draw
     *
     * Returns:
     * {DOMElement}
     */    
    draw: function() {
        OpenLayers.Control.prototype.draw.apply(this, arguments);
        for (var i = 0; i < this.controls.length; i++) {
            this.map.addControl(this.controls[i]);
            this.controls[i].deactivate();
        }
        this.activate();
        return this.div;
    },

    /**
     * Method: redraw
     */
    redraw: function() {
        this.div.innerHTML = "";
        if (this.active) {
            for (var i = 0; i < this.controls.length; i++) {
                var element = this.controls[i].panel_div;
                if (this.controls[i].active) {
                    element.className = this.controls[i].displayClass + "ItemActive";
                } else {    
                    element.className = this.controls[i].displayClass + "ItemInactive";
                }    
                this.div.appendChild(element);
            }
        }
    },

    /**
     * APIMethod: activateControl
     * 
     * Parameters:
     * control - {<OpenLayers.Control>}
     */
    activateControl: function (control) {
        if (!this.active) { return false; }
        if (control.type == OpenLayers.Control.TYPE_BUTTON) {
            control.trigger();
            return;
        }
        if (control.type == OpenLayers.Control.TYPE_TOGGLE) {
            if (control.active) {
                control.deactivate();
            } else {
                control.activate();
            }
            return;
        }
        for (var i = 0; i < this.controls.length; i++) {
            if (this.controls[i] == control) {
                control.activate();
            } else {
                if (this.controls[i].type != OpenLayers.Control.TYPE_TOGGLE) {
                    this.controls[i].deactivate();
                }
            }
        }
        this.redraw();
    },

    /**
     * APIMethod: addControls
     * To build a toolbar, you add a set of controls to it. addControls
     * lets you add a single control or a list of controls to the 
     * Control Panel.
     *
     * Parameters:
     * controls - {<OpenLayers.Control>} 
     */    
    addControls: function(controls) {
        if (!(controls instanceof Array)) {
            controls = [controls];
        }
        this.controls = this.controls.concat(controls);
        
        // Give each control a panel_div which will be used later.
        // Access to this div is via the panel_div attribute of the 
        // control added to the panel.
        // Also, stop mousedowns and clicks, but don't stop mouseup,
        // since they need to pass through.
        for (var i = 0; i < controls.length; i++) {
            var element = document.createElement("div");
            var textNode = document.createTextNode(" ");
            controls[i].panel_div = element;
            OpenLayers.Event.observe(controls[i].panel_div, "click", 
                OpenLayers.Function.bind(this.onClick, this, controls[i]));
            OpenLayers.Event.observe(controls[i].panel_div, "mousedown", 
                OpenLayers.Function.bindAsEventListener(OpenLayers.Event.stop));
        }    

        if (this.map) { // map.addControl() has already been called on the panel
            for (var i = 0; i < controls.length; i++) {
                this.map.addControl(controls[i]);
                controls[i].deactivate();
            }
            this.redraw();
        }
    },
   
    /**
     * Method: onClick
     */
    onClick: function (ctrl, evt) {
        OpenLayers.Event.stop(evt ? evt : window.event);
        this.activateControl(ctrl);
    },

    CLASS_NAME: "OpenLayers.Control.Panel"
});

