from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource


class tds_form(models.Model):
    _name = 'tds.form'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    employee_id = fields.Many2one('hr.employee', string='Employee',default=_default_employee)
    tds_o2m = fields.One2many('tds.heads','form_id',string='Declarations')
    tds_heads_line = fields.One2many('tds.heads.line', 'tds_form_id', string='Allowance')
    total_amount = fields.Float('Total Amount', compute='compute_total')
    other_income = fields.Float('Other Income Amount',size=10)
    other_income_desc = fields.Text('Description',size=300)
    
    emp_id = fields.Char('Employee ID',size=10)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')]) 
    fiscal_year_id = fields.Many2one('fiscal.year',domain=[('active','=',True)])
    state = fields.Selection([('draft','Draft'),('request','Requested'),('approve','Approved'),('cancel','Cancel')],string="Status", default='draft', track_visibility='onchange')
    
    
    @api.multi
    def to_request(self):
        for record in self:
            record.state = 'request'
            
    @api.multi
    def to_approve(self):
        for record in self:
            record.state = 'approve'
            
    @api.multi
    def to_cancel(self):
        for record in self:
            record.state = 'cancel'
    
    @api.onchange('employee_id')
    def onchange_employee_id_value(self):
        for record in self:
            if record.employee_id:
                record.emp_id = record.employee_id.emp_id
                record.branch_id = record.employee_id.branch_id.id
                
    

    @api.multi
    @api.depends('tds_heads_line.amount')
    def compute_total(self):
        for rec in self:
            rec.total_amount = sum(line.amount for line in rec.tds_heads_line)

    @api.constrains('employee_id', 'fiscal_year_id')
    def check_fiscal_year_id_employee_id(self):
        for record in self:
            if len(record.search([('employee_id','=',record.employee_id.id),('fiscal_year_id','=',record.fiscal_year_id.id),('state','!=','cancel')]).ids) > 1:
                raise ValidationError("TDS Declaration are already set for this Fiscal Year")
            
    @api.constrains('other_income', 'total_amount')
    def check_other_income_total_amount(self):
        for record in self:
            if record.other_income < 0:
                raise ValidationError("Other Income Amount should not be a Negative value ")
            if record.total_amount < 0:
                raise ValidationError("Total Amount should not be a Negative value ")

class tds_heads(models.Model):
    _name = 'tds.heads'

    name = fields.Char('Head Name',size=100)
    head_id = fields.Many2one('tds.heads.master')
    max_allowed_amount = fields.Float('Maximum Allowed Amount',size=10)
    total_amount = fields.Float('Total Amount', compute='compute_total')
    tds_heads_line_o2m = fields.One2many('tds.heads.line', 'tds_head_id', string='Allowance')
    form_id = fields.Many2one('tds.form')


    @api.multi
    @api.onchange('head_id')
    def onchange_head(self):
        if self.head_id:
            self.name = self.head_id.name
            self.max_allowed_amount = self.head_id.amount

    @api.multi
    @api.depends('tds_heads_line_o2m.amount')
    def compute_total(self):
        for rec in self:
            rec.total_amount = sum(line.amount for line in rec.tds_heads_line_o2m)
            if rec.total_amount > rec.max_allowed_amount:
                raise ValidationError('Total amount should be lesser than Maximum Allowed Amount')

    @api.one
    @api.constrains('total_amount')
    def validate_total_max(self):
        if self.total_amount > self.max_allowed_amount:
            raise ValidationError('Total amount should be lesser than Maximum Allowed Amount')

    @api.constrains('max_allowed_amount','total_amount')
    def check_max_allowed_total_amount(self):
        for record in self:
            if record.max_allowed_amount < 0:
                raise ValidationError("Maximum Allowed Amount should not be a Negative value ")
            if record.total_amount < 0:
                raise ValidationError("Total Amount should not be a Negative value ")


class tds_heads_line(models.Model):
    _name = 'tds.heads.line'

    # name = fields.Char('TDS Allowance Name')
    name = fields.Many2one('tds.heads.allowance.master',string='TDS Allowance Name')
    amount = fields.Float('Amount')
    tds_head_id = fields.Many2one('tds.heads', string='TDS Head')
    tds_form_id = fields.Many2one('tds.form')
    filename = fields.Char('Attachment Name',size=100)
    attachment = fields.Binary('Proof Attachment', attachment=True)

    @api.constrains('amount')
    def check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError("Total Amount should not be Negative ")

    @api.constrains('amount')
    def check_amount_by_head(self):
        for record in self:
            if record.amount:

                for heads_line in record.tds_form_id.tds_heads_line:
                    if heads_line.amount > heads_line.name.amount and heads_line.name.amount > 0:
                        raise ValidationError(_("Maximum Allowed Amount(%s) has exceeded for %s")%(heads_line.name.amount,heads_line.name.name))

                # heads = record.env['tds.heads.master'].search([])
                # for head in heads:
                #     amount = 0.0
                #     for heads_line in record.tds_form_id.tds_heads_line:
                #         if head.id == heads_line.name.head_master_id.id:
                #             amount += heads_line.amount
                #         print ("1111111111111111111",heads_line, heads_line.amount)
                #     if head.amount < amount:
                #         raise ValidationError("TDS Heads Amount has exceeded than the Maximum allowed amount")


class tds_heads_master(models.Model):
    _name = 'tds.heads.master'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'

    name = fields.Char('Head Name',size=100)
    code = fields.Char('Code',size=50)
    amount = fields.Float('Maximum allowed amount',size=10)
    description = fields.Text('Description', size=100)
    tds_allowance_head_line = fields.One2many('tds.heads.allowance.master','head_master_id',string='Allowance Head')

    @api.constrains('amount')
    def check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError("Maximum Allowed Amount should not be Negative ")


class tds_heads_allowance_master(models.Model):
    _name = 'tds.heads.allowance.master'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'

    name = fields.Char('TDS Allowance Name',size=100)
    amount = fields.Float('Maximum allowed amount')
    head_master_id = fields.Many2one('tds.heads.master', "Type Under")
    description = fields.Text('Description', size=100)

    @api.constrains('amount')
    def check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError("Maximum Allowed Amount should not be Negative ")
            if record.head_master_id:
                if record.head_master_id.amount > 0.00:
                    if record.amount > record.head_master_id.amount:
                        raise ValidationError("Maximum Allowed Amount should not exceed the Amount mentioned in Type Under ")
                    
                    allowance_ids = record.search([('head_master_id','=',record.head_master_id.id)])
                    amount = 0.00
                    amount_list = []
                    for allowance in allowance_ids:
                        if allowance.amount:
                            amount += allowance.amount
                            amount_list.append(allowance.name + ':' + str(allowance.amount) )
                            
                    if amount > record.head_master_id.amount:
                        raise ValidationError("Maximum Allowed Amount should not exceed the Amount mentioned in Type Under ")
                    
#                         raise ValidationError(_("Maximum Allowed Amount should not exceed the Amount mentioned in Type Under" /
#                         "Already following allowance configure mentioned in Type Under %s " )%(i for i in amount_list:))

#########################################################################################

class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    tds_declaration_amount = fields.Float('TDS Declared Amount (per year)', compute="compute_declared_amt")
    other_income_amount = fields.Float('Other Income Amount', compute="compute_declared_amt")

    @api.multi
    @api.depends('tds_declaration_amount')
    def compute_declared_amt(self):
        for rec in self:
            fiscal_year_id = self.env['fiscal.year'].search([('active','=',True)])
            td_em = self.env['tds.form'].search([('employee_id','=',self.employee_id.id),('state','=','approve'),('fiscal_year_id','=',fiscal_year_id.id)])
            if td_em:
                self.tds_declaration_amount = td_em.total_amount
                self.other_income_amount = td_em.other_income

# 
# class hr_contract_inherit(models.Model):
#     _inherit = 'hr.contract'
# 
#     # ctc = fields.Float('CTC')
#     # per_of_wage = fields.Float('Basic (%)')
#     #
#     # @api.onchange('per_of_wage', 'ctc')
#     # def onchange_percentage(self):
#     #     if self.ctc > 0.0 and self.per_of_wage > 0.0:
#     #         self.wage = self.ctc * ((self.per_of_wage/12) / 100)
# 
#     @api.one
#     @api.constrains('employee_id')
#     def _check_unique_employee_id(self):
#         if self.employee_id:
#             if len(self.search([('employee_id','=',self.employee_id.id)])) > 1:
#                 raise ValidationError("Contract record is already exists for selected Employee.")
