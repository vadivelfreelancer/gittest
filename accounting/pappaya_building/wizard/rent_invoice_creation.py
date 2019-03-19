from odoo import api, models, fields, _

class RentInvoiceCreation(models.TransientModel):
    _name = 'rent.invoice.creation'

    rent_ids = fields.Many2many('rent.creation', string="Rent")

    @api.model
    def default_get(self, fields_list):
        res = {}
        context = self._context or {}
        rent_obj = self.env['rent.creation'].browse(context.get('active_ids', []))
        res['rent_ids'] = rent_obj.ids if rent_obj else []
        return res

    @api.multi
    def action_create_invoice(self):
        context = self._context or {}
        rent_obj = self.env['rent.creation'].browse(context.get('active_ids', []))
        for obj in rent_obj:
            if obj.state == 'confirmed':
                prod = {}
                prod['name'] = 'Service Product'
                prod['type'] = 'service'
                prod_obj = self.env['product.product'].search([('name','=','Services Product')])
                if prod_obj:
                    product_id = prod_obj
                else:
                    product_id = self.env['product.product'].create(prod)
                account_id = self.env['account.account'].search(['|',('name','=','Buildings'),('code','=','101100')])
                # account_id = self.env['ir.model.data'].get_object_reference('l10n_in', 'p1011')[1]
                vals={}
                vals['partner_id'] = obj.partner_id.id
                # vals['reference'] = 'Building: ' + str(obj.building_id.name)
                vals['date_invoice'] = obj.date
                vals['amount_untaxed'] = obj.building_rent + obj.building_maintenance_amt
                vals['type'] = 'in_invoice'
                print ('vals', vals)
                inv_obj = self.env['account.invoice'].create(vals)
                line_vals = {}
                line_vals['product_id'] = product_id.id
                line_vals['name'] = 'Owner:' + str(obj.partner_id.name) + ' ' + 'Building: ' + str(obj.building_id.name)
                line_vals['price_unit'] = obj.total_amt
                line_vals['account_id'] = account_id.id
                line_vals['invoice_id'] = inv_obj.id
                self.env['account.invoice.line'].create(line_vals)
                inv = {}
                inv['owner_id'] = obj.owner_id.id
                inv['partner_id'] = obj.partner_id.id
                inv['branch_id'] = obj.branch_id.id
                inv['building_id'] = obj.building_id.id
                inv['block_id'] = obj.block_id.id
                inv['floor_id'] = obj.floor_id.id
                inv['room_id'] = obj.room_id.id
                inv['building_rent'] = obj.building_rent
                inv['building_maintenance_amt'] = obj.building_maintenance_amt
                inv['total_amt'] = obj.total_amt
                inv['state'] = 'invoiced'
                inv['date'] = obj.date
                inv['generated_date'] = fields.Date.today()
                self.env['rent.generation'].create(inv)
                rent_obj.write({'state':'invoiced'})



