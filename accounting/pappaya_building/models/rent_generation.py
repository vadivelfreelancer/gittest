from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class RentGeneration(models.Model):
    _name = 'rent.generation'
    _description = 'Rent Generation'

    name = fields.Char(size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string='Building')
    building_rent = fields.Float(string='Building Rent')
    building_maintenance_amt = fields.Float(string='Building Maintenance Amount')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('invoiced', 'Invoiced')], default='draft', string='State')
    month = fields.Selection([('jan', 'January'), ('feb', 'February'), ('mar', 'March'),('apr', 'April'), ('may', 'May'), ('jun', 'June'),('jul', 'July'), ('aug', 'August'), ('sep', 'September'),('oct', 'October'), ('nov', 'November'), ('dec', 'December')], string='Month')
    year = fields.Selection([(num, str(num)) for num in reversed(range(2016, (datetime.now().year) + 10))], 'Year',
                            default=2019, )
    date = fields.Date('Date')
    rent_ids = fields.One2many('rent.generation.line', 'rent_generation_id')
    is_rent = fields.Boolean()

    @api.onchange('building_id')
    def onchange_building(self):
        if self.building_id:
            self.building_rent = self.building_id.rent
            self.building_maintenance_amt = self.building_id.maintenance_amount
        
    @api.multi
    def search_rent(self):
        if self.rent_ids:
            self.rent_ids.unlink()
        existing_gen_ids = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('month','=',self.month),('year','=',self.year),('id','!=',self.id),('state','!=','draft')])
        if existing_gen_ids:
                raise ValidationError(_("Rent is already Created for this month"))
        new_sequence_code = 'rent.generation'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        owner_ids = self.env['pappaya.owner'].search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id)])
        if owner_ids:
            sno = 1
            for owner in owner_ids:
                vals = {
                    'sno':sno,
                    'owner_name':owner.owner_id.name,
                    'rent_amt':owner.rent + owner.arrear_amount if owner.arrear_amount else owner.rent,
                    'gst_amt':owner.rent + owner.arrear_amount if owner.is_gst_registered == 'yes' else 0.0,
                    'maintenence_amt': owner.maintanance_amt,
                    'gst_maintenance_amt':owner.maintanance_amt if owner.is_gst_registered == 'yes' else 0.0,
                    'outstanding_advance':0.0,
                    'advance_amt':0.0,
                    'rent_tds': owner.rent + owner.arrear_amount * 0.1,
                    'maintenence_tds':owner.maintanance_amt * 0.1,
                    'gstin':owner.gst_no,
                    'invoice_no':'',
                    'date':False,
                    'rent_generation_id':self.id,
                    'owner_id':owner.id,
                    }
                self.env['rent.generation.line'].create(vals)
                sno +=1

    @api.multi
    def write(self, vals):
        if 'rent_ids' in vals:
            for rec in vals['rent_ids']:
                if rec[2] and rec[2]['rent_amt']:
                    line = self.env['rent.generation.line'].browse(rec[1])
                    if rec[2]['rent_amt'] < line.owner_id.rent:
                        arrear = line.owner_id.arrear_amount + (line.owner_id.rent - rec[2]['rent_amt'])
                        line.owner_id.write({'arrear_amount':arrear})
                if rec[2] and rec[2]['maintenence_amt']:
                    line = self.env['rent.generation.line'].browse(rec[1])
                    if rec[2]['maintenence_amt'] < line.owner_id.maintanance_amt:
                        _maintenance_arrear = line.owner_id.maintenance_arrears_amt + (line.owner_id.maintanance_amt - rec[2]['maintenence_amt'])
                        line.owner_id.write({'maintenance_arrears_amt':_maintenance_arrear})
        return super(RentGeneration, self).write(vals)
        
class RentGenerationLine(models.Model):
    _name = 'rent.generation.line'
    _description = 'Rent Generation Line'

    sno = fields.Integer(stirng='SNO')
    owner_name = fields.Char('Owner Name')
    owner_id = fields.Many2one('pappaya.owner')
    rent_amt = fields.Float('Rent Amt')
    gst_amt = fields.Float('GST-Rent')
    maintenence_amt = fields.Float('Maintenance Amt')
    gst_maintenance_amt = fields.Float('GST-Main.Amt')
    outstanding_advance = fields.Float('Outstanding Advance')
    advance_amt = fields.Float('Advance Amt')
    rent_tds = fields.Float('Rent TDS')
    maintenence_tds = fields.Float('Maintenance TDS')
    gstin = fields.Char('GSTIN')
    invoice_no = fields.Char('Invoice No')
    date = fields.Date('Invoice Date')
    rent_generation_id = fields.Many2one('rent.generation') 
    
    @api.onchange('rent_amt')
    def onchange_rent_amt(self):
        if self.rent_amt and (self.rent_amt < self.owner_id.rent):
            self.gst_amt = self.rent_amt
            self.rent_tds = self.rent_tds * 0.1
