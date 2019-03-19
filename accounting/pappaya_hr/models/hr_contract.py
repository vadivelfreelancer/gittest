from odoo import api, fields, models, tools, _
from datetime import datetime,date
from odoo.exceptions import UserError, ValidationError

class HrContractWage(models.TransientModel):
    _name = 'hr.contract.wage'
    _description = 'Contract Wage Updation'

    wage_amount = fields.Integer('New Wage')
    update_reason = fields.Char('Reason for Wage Updation',size=100)

    @api.multi
    def update_contract_wage(self):
        contract = self.env['hr.contract'].search([('id','=',self._context.get('active_id'))])
        contract.write({
            'wage' : self.wage_amount,
            'wage_history_line': [(0, 0, {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'user_id': self.env.user.id,
                'old_wage': contract.wage,
                'new_wage': self.wage_amount,
                'update_reason': self.update_reason
            })]
        })

class HRContract(models.Model):
    _inherit = 'hr.contract'

    wage_history_line = fields.One2many('hr.contract.wage.line','contract_id', string='Wage History')
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])


class HRContractWageHistory(models.Model):
    _name = 'hr.contract.wage.line'

    contract_id = fields.Many2one('hr.contract', string='Contract')
    date = fields.Datetime('Date')
    new_wage = fields.Integer('New Wage')
    old_wage = fields.Integer('Old Wage')
    user_id = fields.Many2one('res.users', string='User')
    update_reason = fields.Char('Reason for Wage Updation',size=100)
    
    
class ContractType(models.Model):
    _inherit = 'hr.contract.type'

    name = fields.Char(string='Type of Employment', required=True,size=100)
    sequence_id = fields.Char('Series')
    is_permanent = fields.Boolean('Is Permanent', compute='_get_is_permanent')

    def _get_is_permanent(self):
        for record in self:
            if record.name == 'Permanent':
                record.is_permanent = True
            else:
                record.is_permanent = False
    
    
    @api.model
    def create(self, vals):
        
        sequence_config =self.env['meta.data.master'].search([('name','=','category')])
        if not sequence_config:
            raise ValidationError(_("Please Configure Category Sequence"))
        vals['sequence_id'] = self.env['ir.sequence'].sudo().next_by_code('pappaya.category') or _('New')
        res = super(ContractType, self).create(vals)
        return res

    @api.constrains('is_permanent')
    def check_is_permanent(self):
        for record in self:
            if len(record.search([('is_permanent', '=', True)])) > 1:
                raise ValidationError("Is Permanent record already exists")

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', 'ilike', self.name)])) > 1:
            raise ValidationError("Name already exists")

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            raise ValidationError("Sorry, You are not allowed to rename it.\nThis record is considered as master configuration.")
