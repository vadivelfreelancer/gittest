from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class BuildingAdvanceVacation(models.Model):
    _name = 'building.vacation'
    _description = 'Building Advance Vacation/ShutDown'

    name = fields.Char(size=40)
    apex_id = fields.Many2one('operating.unit', string="Apex",domain=[('type','=','entity')])
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string="Building Name")
    owner_id = fields.Many2one("pappaya.owner", string='Owner Name')
    date = fields.Date(string='Date')
    narration = fields.Char('Narration',size=40)
    transactions = fields.Char('Transactions',size=40)
    type = fields.Selection([('advance', 'Advance'), ('deposit', 'Security Deposit')], default='advance')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    building_vacation_ids = fields.One2many('building.vacation.line', 'building_vacation_id')
    from_month = fields.Selection([('jan', 'January'), ('feb', 'February'), ('mar', 'March'),('apr', 'April'), ('may', 'May'), ('jun', 'June'),('jul', 'July'), ('aug', 'August'), ('sep', 'September'),('oct', 'October'), ('nov', 'November'), ('dec', 'December')], string='From Month')
    from_year = fields.Selection([(num, str(num)) for num in reversed(range(2016, (datetime.now().year) + 10))], 'Year',
                            default=2019, )

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'building.shutdown'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        
    @api.onchange('apex_id')
    def _onchange_apex(self):
        if self.apex_id:
            return {'domain': {'branch_id_id': [('parent_id', '=', self.apex_id.id)]}}
        else:
            return {}
        
    @api.multi
    def search_building_vacation(self):
        existing_vacation = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id),('type','=',self.type),('state','=','approved')])
        if existing_vacation:
            raise ValidationError(_("Building is already closed for this owner"))
        if self.building_vacation_ids:
            self.building_vacation_ids.unlink()
        existing_gen_ids = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('from_month','=',self.from_month),('from_year','=',self.from_year),('id','!=',self.id),('state','=','approved')])
        if existing_gen_ids:
                raise ValidationError(_("Building is in closed"))
        if self.type == 'deposit':
            deposit = self.env['security.deposit'].search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id)])
            if deposit:
                vals = {
                    'sno':1,
                    'owner_name':self.owner_id.owner_id.name,
                    'paid_amt':deposit.repayment_amount,
                    'outstanding_amt':deposit.available_amount - deposit.repayment_amount,
                    'adjust_amt':0.0,
                    'tds_amt':(deposit.available_amount - deposit.repayment_amount )* 0.1,
                    'building_vacation_id':self.id,
                    'owner_id':self.owner_id.id,
                    'total_amt':deposit.available_amount - deposit.repayment_amount,
                    }
                self.env['building.vacation.line'].create(vals)
        else:
            advance = self.env['building.advance'].search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id)])
            if advance:
                vals = {
                    'sno':1,
                    'owner_name':self.owner_id.owner_id.name,
                    'paid_amt':advance.repayment_advance,
                    'outstanding_amt':advance.available_advance - advance.repayment_advance,
                    'adjust_amt':0.0,
                    'tds_amt':(advance.available_advance - advance.repayment_advance )* 0.1,
                    'building_vacation_id':self.id,
                    'owner_id':self.owner_id.id,
                    'total_amt': advance.available_advance - advance.repayment_advance,
                    }
                self.env['building.vacation.line'].create(vals)
            
class BuildingVacationLine(models.Model):
    _name = 'building.vacation.line'
    _description = 'Building Vacation Line'

    sno = fields.Integer(stirng='SNO')
    owner_name = fields.Char('Owner Name')
    owner_id = fields.Many2one('pappaya.owner')
    paid_amt = fields.Float('Paid Amount')
    outstanding_amt = fields.Float('Outstanding Amount')
    adjust_amt = fields.Float('Adjust Amt')
    tds_amt = fields.Float('TDS Amount')
    total_amt = fields.Float()
    building_vacation_id = fields.Many2one('building.vacation')
    
    @api.onchange('adjust_amt')
    def onchange_adjust_amt(self):
        if self.adjust_amt and self.adjust_amt > 0:
            self.outstanding_amt = self.total_amt - self.adjust_amt
            self.tds_amt = self.outstanding_amt * 0.1
            
