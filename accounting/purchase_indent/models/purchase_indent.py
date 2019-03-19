# -*- coding: utf-8 -*-

# from . import datetime
# from datetime import datetime
from datetime import datetime, date, timedelta
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
#import googlemaps
from odoo.exceptions import UserError, ValidationError


class PurchaseIndent(models.Model):
    _name = "purchase.indent"

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('purchase.indent') or '/'
        return super(PurchaseIndent, self).create(vals)
    
    @api.model
    def _default_branch(self):
        user_id = self.env['res.users'].sudo().browse(self.env.uid)
        if user_id.company_id:
            return user_id.id
    
    res_partner = fields.Many2one('res.partner', string="Requesting Branch",default=lambda self: self.env.user.partner_id.id)
    name = fields.Char(string='name', readonly=True, copy=False)
    branch_location_id = fields.Many2one('stock.location', string="Branch")
    indent_date = fields.Datetime(string='Indent Date', required=True, default=fields.Datetime.now, readonly=True,
                                  states={'draft': [('readonly', False)]})
    required_date = fields.Datetime(string='Required Date', required=True, readonly=True, default=fields.Datetime.now,
                                    states={'draft': [('readonly', False)]})
    issued_date = fields.Datetime(string='Approve Date', readonly=True)
    issued_by = fields.Many2one('res.users', string='Issued by', readonly=True)
    requirement = fields.Selection([('1', 'Ordinary'), ('2', 'Urgent')], 'Requirement', readonly=True, default='1',
                                   states={'draft': [('readonly', False)]})
    item_for = fields.Selection([('purchase', 'Produce'), ('other', 'Other')], string='Order for', default='other',
                                readonly=True, states={'draft': [('readonly', False)]})
    move_lines = fields.One2many('stock.move', 'purchase_indent_id', string='Moves', copy=False, readonly=True)
    product_lines = fields.One2many('purchase.indent.product.lines', 'indent_id', string='Product', copy=False)
    description = fields.Text(string='Additional Information', readonly=True,
                              states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Requesting Branch', default=lambda self: self.env.user.company_id,
                                 readonly=True, states={'draft': [('readonly', False)]})
    location_id = fields.Many2one('stock.location')

    state = fields.Selection(
            [('draft', 'Draft'),
             ('waiting_approval', 'Waiting for Approval'),
             ('inprogress', 'Ready to Transfer'),
             ('move_created', 'Moves Created'),
             ('done', 'Done'),
             ('cancel', 'Cancel'),
             ('reject', 'Rejected')], string='State', readonly=True, default='draft', track_visibility='onchange')
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group', copy=False)
    requesting_person_name = fields.Char('Requesting Person Name', size=30)
    indent_creator_name = fields.Char('Indent Creator Name', size=30)
    store_type = fields.Selection([('mess', 'Mess'),('nonmess','Non Mess')], string='Store Type')

    @api.multi
    def purchase_indent_confirm(self):
        for indent in self:
            if indent.item_for == 'purchase':
                if not indent.move_lines:
                    raise exceptions.Warning(_("Warning "
                                               "You cannot confirm an indent %s which has no line." % indent.name))
                else:
                    indent.write({'state': 'waiting_approval'})
            else:
                if not indent.product_lines:
                    raise exceptions.Warning(_("Warning "
                                               "You cannot confirm an indent %s which has "
                                               "no product line." % indent.name))
                else:
                    indent.write({'state': 'waiting_approval'})

    @api.one
    def purchase_indent_inprogress(self):
        todo = []
        for o in self:
            if not any(line for line in o.product_lines):
                raise exceptions.Warning(_('Error!'),
                              _('You cannot Approve a order without any order line.'))

            for line in o.product_lines:
                if line:
                    todo.append(line.id)

        appr_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.env['purchase.indent.product.lines'].action_confirm(todo)

        for id in self.ids:
            self.write({'state': 'inprogress', 'issued_date': appr_date})
        return True

    @api.one
    def indent_reject(self):
        if self.move_lines:
            for line in self.move_lines:
                if line.state == 'cancel':
                    pass
                elif line.state == 'done':
                    pass
                else:
                    line.action_cancel()
        self.write({'state': 'reject'})

    def get_tot_qty(self):
        tot_qty = 0
        move_lines_obj = self.env['stock.move']
        if self.product_lines:
            for line in self.product_lines:
                if line.product_id.type != 'service':
                    if line.location_id:
                        if line.location_dest_id:
                            tot_qty = 0
                            obj_quant = self.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                                        ('location_id', '=', line.location_id.id)])
                            for obj in obj_quant:
                                tot_qty += obj.quantity
        return tot_qty

    @api.multi
    def indent_transfer(self):
        print ("transfer")
        name = self.name
        move_lines_obj = self.env['stock.move']
        if self.product_lines:
            for line in self.product_lines:
                if line.product_id.type != 'service':
                    if line.location_id:
                        if line.location_dest_id:
                            tot_qty = 0
                            obj_quant = self.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                                        ('location_id', '=', line.location_id.id)])
                            for obj in obj_quant:
                                tot_qty += obj.quantity
                            move_line = {}
                            if line.product_id.type == 'consu':
                                move_line = {
                                    'product_id': line.product_id.id,
                                    'state': "draft",
                                    'product_uom_qty': line.product_uom_qty,
                                    'product_uom': line.product_id.uom_id.id,
                                    'name': line.product_id.name,
                                    'location_id': line.location_id.id,
                                    'location_dest_id': line.location_dest_id.id,
                                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'date_expected': self.required_date,
                                    'invoice_state': "none",
                                    'origin': name,
                                    'purchase_indent_id': self.id
                                }
                                move_lines_obj.create(move_line)
                            else:
                                move_line = {}
                                if tot_qty >= line.product_uom_qty:
                                    move_line = {
                                                'product_id': line.product_id.id,
                                                'state': "draft",
                                                'product_uom_qty': line.product_uom_qty,
                                                'product_uom': line.product_id.uom_id.id,
                                                'name': line.product_id.name,
                                                'location_id': line.location_id.id,
                                                'location_dest_id': line.location_dest_id.id,
                                                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                'date_expected': self.required_date,
                                                'invoice_state': "none",
                                                'origin': name,
                                                'purchase_indent_id': self.id
                                                }
                                    move_lines_obj.create(move_line)
                                else:
                                    # self._action_po_create()

                                    if tot_qty:
                                        raise exceptions.Warning((" No sufficient stock for product ' %s ' in '%s'.  "
                                                                  "Available quantity is %s %s.") %
                                                                 (line.product_id.name, line.location_id.name, tot_qty,
                                                                  line.product_uom.name))
                                    else:
                                        raise exceptions.Warning(
                                                      (" No stock for product ' %s ' in '%s'."
                                                       "  Please continue with another location ") % (line.product_id.name,
                                                                                                      line.location_id.name))
                        else:
                            raise exceptions.Warning((" Destination Location is not set properly for' %s '. "
                                                      "So Plese cancel this indent and create a new one please.")
                                                     % line.product_id.name)
                    else:
                        raise exceptions.Warning(("Source Location is not set properly for ' %s '.  "
                                                  "Please go and set Source Location.")
                                                 % line.product_id.name)
                else:
                    raise exceptions.Warning("This product is a service type product.")
        else:
            raise exceptions.Warning('You cannot Transfer a order without any product line.')
        self.write({'state': 'move_created'})

    @api.multi
    def _action_po_create(self):
        print ("Action Before method ******************")
        self.product_lines._action_procurement_create()

    @api.multi
    def indent_transfer_move_confirm(self):
        if self.move_lines:
            for line in self.move_lines:
                if line.state == 'cancel':
                    pass
                elif line.state == 'done':
                    pass
                else:
                    # line.action_done()
                    line._action_confirm()
                    line._action_assign()
                    line.move_line_ids.write({'qty_done': line.product_uom_qty}) 
                    line._action_done()
        else:
            raise Warning(_('You cannot Confirm a order without any move lines.'))
        self.write({'state': 'done'})

    def _prepare_procurement_group(self):
        return {'name': self.name}


# purchase button action
    @api.multi
    def prepare_order_line_purchase_order(self):
        purchase_orders1 = self.env['purchase.order']

        val = {}
        for ids in self.product_lines.product_id.seller_ids :
            val=({
                'partner_id': ids.name.id
                })
            po_order1 = purchase_orders1.create(val)

            if self.product_lines.product_uom_qty > self.get_tot_qty() :
                values = {
                            'price_unit': self.product_lines.product_id.list_price or 0.0, 
                            'product_id': self.product_lines.product_id.id,
                            'product_uom': self.product_lines.product_uom.id,
                            'product_qty': self.product_lines.product_uom_qty - self.get_tot_qty(),
                            'name': self.product_lines.name, 
                            'date_planned': datetime.now(),
                            'order_id' : po_order1.id
                            }
            else :
                values = {
                            'price_unit': self.product_lines.product_id.list_price or 0.0, 
                            'product_id': self.product_lines.product_id.id,
                            'product_uom': self.product_lines.product_uom.id,
                            'product_qty': self.product_lines.product_uom_qty,
                            'name': self.product_lines.name, 
                            'date_planned': datetime.now(),
                            'order_id' : po_order1.id
                            }


            purchase_line_obj = self.env['purchase.order.line']

            po_line = purchase_line_obj.create(values)
 
        search_ids = self.env['purchase.order'].search([])
        last_id = search_ids and max(search_ids) 
        return {
                'name': _('Revise Quote'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'res_id': last_id.id,
                'type': 'ir.actions.act_window',
            }




class IndentProductLines(models.Model):
    _name = 'purchase.indent.product.lines'
    _description = 'Indent Product Lines'
   
#     @api.model
#     def default_get(self, fields):
#         data = super(IndentProductLines, self).default_get(self)
#         required_res_partner = self._context.get('required_res_partner', False)
#         if required_res_partner:
#             data['res_partner'] = required_res_partner
#         return data
    
    @api.one
    def action_confirm(self, todo):
        self.write({'state': 'inprogress'})
        return True
    
    def get_distance(self, frm, to):
        gmaps = googlemaps.Client(key='AIzaSyCEMtT5M-tqfgNUw9Tedaf0VyXeTuia_2Q')
        if frm and to:
            my_dist = gmaps.distance_matrix(frm, to)['rows'][0]['elements'][0]
            print(my_dist)
            #{'status': 'OK', 'distance': {'value': 145446, 'text': '145 km'}, 'duration': {'value': 10632, 'text': '2 hours 57 mins'}}
            if my_dist['status'] == 'OK':
                return my_dist
                
        

#         print("Distance",  my_dist["distance"]["text"])
#         print("Time",  my_dist["duration"]["text"]) 
        
    res_partner = fields.Many2one('res.partner', string="Requesting Branch")
    company_id = fields.Many2one('res.company', string='Company',compute="compute_location_dest")
    indent_id = fields.Many2one('purchase.indent', string='Indent', required=True, ondelete='cascade')
    name = fields.Text(string='Description', required=True, readonly=True,
                       states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    product_id = fields.Many2one('product.product', string='Product', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    original_product_id = fields.Many2one('product.product', string='Product to be Manufactured', readonly=True,
                                          states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    product_uom_qty = fields.Float(string='Quantity Required', digits_compute=dp.get_precision('Product UoS'), required=True,
                                   readonly=True, states={'draft': [('readonly', False)],
                                                          'waiting_approval': [('readonly', False)],
                                                          'inprogress': [('readonly', False)]})
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)],
                                          'inprogress': [('readonly', False)]})
    location_id = fields.Many2one('stock.location', string='Source Location', readonly=True,
                                  states={'inprogress': [('readonly', False)]})
#     location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True, readonly=True,
#                                        states={'draft': [('readonly', False)],
#                                                'waiting_approval': [('readonly', False)]})
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', compute='_test_compute_location_dest_id')
    
    delay = fields.Float(string='Lead Time')
    purpose = fields.Text(string='Purpose')
    state = fields.Selection(
            [('draft', 'Draft'),
             ('waiting_approval', 'Waiting for Approval'),
             ('inprogress', 'Ready to Transfer'),
             ('move_created', 'Moves Created'),
             ('done', 'Done'),
             ('cancel', 'Cancel'),
             ('reject', 'Rejected')], string='State', default='draft', related='indent_id.state')

    sequence = fields.Integer('Sequence')
    procurement_ids = fields.One2many('stock.move', 'sale_line_id', string='Procurements')
    current_location_ids = fields.One2many('stock.current.locations', 'indent_line_id', string="Test")
   
    
#     @api.depends('res_partner')
#     def set_location(self):
#         
#         current_location = self.env['stock.location'].search([('partner_id','=', partner)])[0]
#         print ("fdsfdsfdsdsddsf",current_location)
#         self.location_dest_id = current_location.id

    @api.constrains('location_id')
    def check_location_name(self):
        for rec in self:
            if rec.location_id:
                if rec.location_id.id == rec.location_dest_id.id:
                    raise ValidationError("Source and destination location should not be same")
    @api.one
    @api.depends('res_partner')
    def _test_compute_location_dest_id(self):
         
        if self.indent_id.res_partner.company_type=='company':
            partner = self.indent_id.res_partner.id
            print (partner)
              
        else:
            partner = self.env.user.parent_id.id
            print (partner)
            
        
        self.res_partner = partner    
        current_location = self.env['stock.location'].search([('partner_id','=', partner),('usage','=','internal')])
        if not current_location:
            raise exceptions.Warning("Warehouse location is not available.")
        location_id = current_location[0]
        self.location_dest_id = location_id.id
    
    @api.onchange('product_id')
    def current_location(self):
        l_list = []
        if self.product_id:
            self.current_location_ids =l_list
            c_location = self.env['stock.quant'].search([('product_id','=',self.product_id.id)])
            print (c_location)
            if c_location:
                for p in c_location:
                    
                    if p.location_id.usage in ['internal','customer'] and p.location_id.partner_id.school_check==True:
                        city = p.location_id.partner_id.city
                        dest_location_city = self.res_partner.city
                        dist_val = "Unable to find the distance"
                        if city and dest_location_city:
                                
                            distance = self.get_distance(city, dest_location_city)
                            try:
                                if distance['status'] == 'OK':
                                    if 'distance' in distance.keys():
                                        if 'text' in distance["distance"].keys():
                                            dist_val = distance["distance"]["text"]
                            except:
                                pass
                            
                        else:
                            dist_val = "Unable to find the distance"
#                         
#                         print (dist_val)
                        l_list.append({'current_location_id': p.location_id.id,
                                        'indent_line_id':self.id,
                                        'city':city or False,
                                        'dest_city':dest_location_city or False,
                                        'distance':dist_val,
                                        'quantity':p.quantity})
                        self.update({'current_location_ids':l_list})
            else:
                raise ValidationError(_("This product is not available in any location"))    
    
   
   

   
                                            
#                     
#             print (l_list)
#             for loct in l_list:
#                 print(loct,"$$$$$$$$")
#                 dest_location_city = self.company_id.city
#                # print(loct['city'], "########", dest_location_city)
#                  
#                 distance = self.get_distance(loct['city'], dest_location_city)
#                 print ("fdssssssssssssssssssssssssss",distance)
#                 print(distance["distance"]["text"])
#                  
#                 self.update({'current_location_ids':l_list.extend({'distance':distance["distance"]["text"]})})
                
                

    #~ def onchange_product_id(self, product_id=False, product_uom_qty=0.0, product_uom=False, name=''):
        #~ product_obj = self.env['product.product']
        #~ value = {}
        #~ if not product_id:
            #~ return {'value': {'product_uom_qty': 1.0, 'product_uom': False,
                              #~ 'name': '', 'specification': '', 'delay': 0.0}}

        #~ product = product_obj.browse(product_id)
        #~ value['name'] = product.name_get()[0][1]
        #~ value['product_uom'] = product.uom_id.id
        #~ value['specification'] = product.name_get()[0][1]

        #~ return {'value': value}
        
        
    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        self.name = self.product_id.description
        return {'domain': {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}
        #return result


    @api.multi
    def _action_procurement_create(self):
        """
        Create procurements based on quantity ordered. If the quantity is increased, new
        procurements are created. If the quantity is decreased, no automated action is taken.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order']  # Empty recordset
        for line in self:
            # if line.state != 'sale' or not line.product_id._need_procurement():
            #     continue
            qty = 0.0
            for proc in line.procurement_ids:
                qty += proc.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            if not line.indent_id.procurement_group_id:
                vals = line.indent_id._prepare_procurement_group()
                line.indent_id.procurement_group_id = self.env["procurement.group"].create(vals)

            vals = line._prepare_order_line_procurement(group_id=line.indent_id.procurement_group_id.id)
            vals['product_qty'] = line.product_uom_qty - qty
            new_proc = self.env["procurement.order"].with_context(procurement_autorun_defer=True).create(vals)
            new_proc.message_post_with_view('mail.message_origin_link',
                values={'self': new_proc, 'origin': line.indent_id},
                subtype_id=self.env.ref('mail.mt_note').id)
            new_procs += new_proc
        new_procs.run()
        return new_procs

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        self.ensure_one()
        return {
            'name': self.name,
            'origin': self.indent_id.name,
            'date_planned': self.indent_id.indent_date,
            'product_id': self.product_id.id,
            'product_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id,
            'company_id': self.indent_id.company_id.id,
            'group_id': group_id,
            'sale_line_id': self.id
        }

class StockMove(models.Model):
    _inherit = 'stock.move'

    purchase_indent_id = fields.Many2one('purchase.indent', 'Indent')
    # move_lines = fields.One2many('stock.move', 'picking_id', string="Stock Moves", copy=True)


class CurrentStockLocation(models.Model):
    _name='stock.current.locations'
    _order='quantity asc'
    
    indent_line_id = fields.Many2one('purchase.indent.product.lines', string="test")
    current_location_id = fields.Many2one('stock.location')
    quantity = fields.Float(string="Available Quantity")
    city = fields.Char(string="city")
    dest_city = fields.Char()
    distance = fields.Char()
