odoo.define('pappaya_fees.fee_structure', function(require) {
"use strict";

var ListView = require('web.ListView');
var ListRenderer = require('web.ListRenderer');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;

//ListView.include({
//	init: function (viewInfo, params) {
//        this._super.apply(this, arguments);
//        
//        var arch = viewInfo.arch;
//        var mode = arch.attrs.editable && !params.readonly ? "edit" : "readonly";
//
//        this.controllerParams.editable = arch.attrs.editable;
//        this.controllerParams.hasSidebar = params.sidebar;
//        this.controllerParams.toolbarActions = viewInfo.toolbar;
//        this.controllerParams.noLeaf = !!this.loadParams.context.group_by_no_leaf;
//        this.controllerParams.mode = mode;
//
//        this.rendererParams.arch = arch;
//        this.rendererParams.hasSelectors =
//                'hasSelectors' in params ? params.hasSelectors : true;
//        this.rendererParams.editable = params.readonly ? false : arch.attrs.editable;
//        
//        this.loadParams.limit = this.loadParams.limit || 80;
//        this.loadParams.type = 'list';
//    },
//});

//alert('44444')
//
//ListRenderer.include({
//	_renderView: function(data) {
//        var self = this;
//        this._super(data);
//        alert('Inside');
//        if (self.model == "pappaya.fees.structure.line") {
//            if (this.fields_view.arch.attrs.class == 'structure_line_ids') {
//               this.$el.find(".oe_list_content > thead:first").replaceWith('<tr class="oe_list_header_columns"> \
//							<th rowspan="2" style="border-left: 1px solid #DFE1E6; background-color:#f0f0f0; color:#4c4c4c; text-align:center;"><div>Date<div></th> \
//            		   		<th rowspan="2" style="border-left: 1px solid #DFE1E6; background-color:#f0f0f0; color:#4c4c4c; text-align:center;"><div>Week Day<div></th> \
//							<th rowspan="2" style="border-left: 1px solid #DFE1E6; background-color:#f0f0f0; color:#4c4c4c; text-align:right;"><div># Emp<div></th> \
//							<th rowspan="2" style="border-left: 1px solid #DFE1E6; background-color:#f0f0f0; color:#4c4c4c; text-align:right;"><div># RG Hours<div></th> \
//	            		    <th rowspan="2" style="border-left: 1px solid #DFE1E6; background-color:#f0f0f0; color:#4c4c4c; text-align:right;"><div># OT Hours<div></th> \
//							</tr>');
//            }
//        
//        }
//    }
//});


});