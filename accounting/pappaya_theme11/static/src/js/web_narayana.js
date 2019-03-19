odoo.define('pappaya_theme11.web_narayana', function(require) {
"use strict";

var BasicRenderer = require('web.BasicRenderer');
var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var dom = require('web.dom');
var field_utils = require('web.field_utils');
var Pager = require('web.Pager');
var utils = require('web.utils');



var _t = core._t;

// Hiding Tooltip for all the fields.
BasicRenderer.include({
    _addFieldTooltip: function (widget, $node) {
        $node = $node.length ? $node : widget.$el;
    },
});
// End

var FIELD_CLASSES = {
    float: 'o_list_number',
    integer: 'o_list_number',
    monetary: 'o_list_number',
    text: 'o_list_text',
};


Pager.include({
	_render: function () {
        var size = this.state.size;
        var current_min = this.state.current_min;
        var current_max = this.state.current_max;

        //if (size === 0 || (this.options.single_page_hidden && this._singlePage())) {
        if (size === 0 || current_max === 0) {
            this.do_hide();
        } else {
            this.do_show();
            this._updateArrows();

            var value = "" + current_min;
            if (this.state.limit > 1) {
                value += "-" + current_max;
            }
            this.$value.html(value);
            this.$limit.html(size);
        }
    },
});

BasicRenderer.include({
	_renderNoContentHelper: function () {
        var $msg = $('<div>')
            .addClass('oe_view_nocontent')
            .html(this.noContentHelp);
//        this.$el.html($msg);
        this.$el.html('No Records Found');
    },
});


var ListRenderer = require('web.ListRenderer');
ListRenderer.include({
	_renderGroupRow: function (group, groupLevel) {
        var aggregateValues = _.mapObject(group.aggregateValues, function (value) {
            return { value: value };
        });
        var $cells = this._renderAggregateCells(aggregateValues);
        if (this.hasSelectors) {
            $cells.unshift($('<td>'));
        }
        var name = group.value === undefined ? _t('Undefined') : group.value;
        var groupBy = this.state.groupedBy[groupLevel];
        
        if (group.fields[groupBy.split(':')[0]].type !== 'boolean') {
            name = name || _t('Undefined');
        } else if (group.fields[groupBy.split(':')[0]].type === 'boolean'){ name = name.toString();}
        // Color code added for groups
        var my_first_string = '<th style="background-color: ';
        var given_group_color = name.split(":")[1];
	    var my_thrid_string = '!important">';
	    var final_header = my_first_string.concat(given_group_color, my_thrid_string);
	    name = name.split(":")[0];
	    // End
        var $th = $('<th>')
                    .addClass('o_group_name')
                    .text(name + ' (' + group.count + ')');
        var $arrow = $('<span>')
                            .css('padding-left', (groupLevel * 20) + 'px')
                            .css('padding-right', '5px')
                            .addClass('fa');
        if (group.count > 0) {
            $arrow.toggleClass('fa-caret-right', !group.isOpen)
                    .toggleClass('fa-caret-down', group.isOpen);
        }
        $th.prepend($arrow);
        if (group.isOpen && !group.groupedBy.length && (group.count > group.data.length)) {
            var $pager = this._renderGroupPager(group);
            var $lastCell = $cells[$cells.length-1];
            $lastCell.addClass('o_group_pager').append($pager);
        }
        // Background image removed for tr tag
        var my_tr = '<tr style="background-image: none ! important; background-color: ';
        var final_header = my_tr.concat(given_group_color, my_thrid_string);         
        // End
        return $(final_header)
                    .addClass('o_group_header')
                    .toggleClass('o_group_open', group.isOpen)
                    .toggleClass('o_group_has_content', group.count > 0)
                    .data('group', group)
                    .append($th)
                    .append($cells);
    },
    
	_renderBodyCell: function (record, node, colIndex, options) {
        var tdClassName = 'o_data_cell';
        if (node.tag === 'button') {
            tdClassName += ' o_list_button';
        } else if (node.tag === 'field') {
            var typeClass = FIELD_CLASSES[this.state.fields[node.attrs.name].type];
            if (typeClass) {
                tdClassName += (' ' + typeClass);
            }
            if (node.attrs.widget) {
                tdClassName += (' o_' + node.attrs.widget + '_cell');
            }
        }
        var $td = $('<td>', {class: tdClassName});

        // We register modifiers on the <td> element so that it gets the correct
        // modifiers classes (for styling)
        var modifiers = this._registerModifiers(node, record, $td, _.pick(options, 'mode'));
        // If the invisible modifiers is true, the <td> element is left empty.
        // Indeed, if the modifiers was to change the whole cell would be
        // rerendered anyway.
        if (modifiers.invisible && !(options && options.renderInvisible)) {
            return $td;
        }

        if (node.tag === 'button') {
            return $td.append(this._renderButton(record, node));
        } else if (node.tag === 'widget') {
            return $td.append(this._renderWidget(record, node));
        }
        if (node.attrs.widget || (options && options.renderWidgets)) {
            var widget = this._renderFieldWidget(node, record, _.pick(options, 'mode'));
            this._handleAttributes(widget.$el, node);
            return $td.append(widget.$el);
        }
        var name = node.attrs.name;
        var field = this.state.fields[name];
        var value = record.data[name];
        var formattedValue = field_utils.format[field.type](value, field, {
            data: record.data,
            escape: true,
            isPassword: 'password' in node.attrs,
        });
        this._handleAttributes($td, node);
		
//		name = formattedValue.toString().split(":")[0];
        return $td.html(formattedValue);
    },
    _onSelectRecord: function (event) {
        event.stopPropagation();
        this._updateSelection();
        if (!$(event.currentTarget).find('input').prop('checked')) {
            this.$('thead .o_list_record_selector input').prop('checked', false);
        }
        else {
            var $nonSelectedRows = this.$('tbody .o_list_record_selector input:checkbox').not(':checked');
                                
          
          if($nonSelectedRows == null || ($nonSelectedRows != null && $nonSelectedRows.size() == 0)) {
                this.$('thead .o_list_record_selector input').prop('checked', true);
            }
            
        }
    },
    
});

});

//~ Disable Right Click
//$(document).ready(function(){
//	$(document).bind("contextmenu",function(e){
//	return false;
//	});
//});
//~ End Disable Right Click
