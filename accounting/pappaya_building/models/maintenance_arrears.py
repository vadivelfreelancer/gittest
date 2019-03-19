from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class MaintenanceArrears(models.Model):
    _name = 'maintenance.arrears'
    _description = 'Maintenance Arrears'

    name = fields.Char(size=40)
    apex_id = fields.Many2one('operating.unit', string="Apex",domain=[('type','=','entity')])
    branch_id = fields.Many2one('operating.unit', string="Branch",domain=[('type','=','branch')])
    building_id = fields.Many2one('pappaya.building', string="Building")
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    from_month = fields.Selection([('jan', 'January'), ('feb', 'February'), ('mar', 'March'),('apr', 'April'), ('may', 'May'), ('jun', 'June'),('jul', 'July'), ('aug', 'August'), ('sep', 'September'),('oct', 'October'), ('nov', 'November'), ('dec', 'December')], string='From Month')
    from_year = fields.Selection([(num, str(num)) for num in reversed(range(2016, (datetime.now().year) + 10))], 'Year',
                            default=2019, )
    to_month = fields.Selection([('jan', 'January'), ('feb', 'February'), ('mar', 'March'),('apr', 'April'), ('may', 'May'), ('jun', 'June'),('jul', 'July'), ('aug', 'August'), ('sep', 'September'),('oct', 'October'), ('nov', 'November'), ('dec', 'December')], string='To Month')
    to_year = fields.Selection([(num, str(num)) for num in reversed(range(2016, (datetime.now().year) + 10))], 'Year',
                            default=2019, )
    maintenance_ids = fields.One2many('maintenance.arrears.line', 'maintenance_arrear_id')

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'maintenance.arrears'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)

    @api.onchange('apex_id')
    def _onchange_apex(self):
        if self.apex_id:
            return {'domain': {'branch_id_id': [('parent_id', '=', self.apex_id.id)]}}
        else:
            return {}
          
    @api.multi
    def search_maintenance_arrears(self):
        if self.maintenance_ids:
            self.maintenance_ids.unlink()
        existing_gen_ids = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('from_month','=',self.from_month),('from_year','=',self.from_year),('to_month','=',self.to_month),('to_year','=',self.to_year),('id','!=',self.id),('state','=','approved')])
        if existing_gen_ids:
                raise ValidationError(_("Maintenance Arrear is already Created for this interval"))
        owner_ids = self.env['pappaya.owner'].search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id)])
        if owner_ids:
            sno = 1
            for owner in owner_ids:
                vals = {
                    'sno':sno,
                    'owner_name':owner.owner_id.name,
                    'maintenence_amt': owner.maintanance_amt,
                    'maintenance_arrears_amt': owner.maintenance_arrears_amt,
                    'tds_amt':owner.maintanance_amt * 0.1,
                    'maintenance_arrear_id':self.id,
                    'owner_id':owner.id,
                    }
                self.env['maintenance.arrears.line'].create(vals)
                sno +=1
  
            
class MaintenanceArrearsLine(models.Model):
    _name = 'maintenance.arrears.line'
    _description = 'Maintenance Arrears Line'

    sno = fields.Integer(stirng='SNO')
    owner_name = fields.Char('Owner Name',size=40)
    owner_id = fields.Many2one('pappaya.owner')
    maintenence_amt = fields.Float('Maintenance Amt')
    maintenance_arrears_amt = fields.Float('Maintenance Arrears Amt')
    tds_amt = fields.Float('Mintenance Arr. TDSAmt')
    maintenance_arrear_id = fields.Many2one('maintenance.arrears')
