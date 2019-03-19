# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil import parser
import math
import re
import calendar

class pappaya_promotion(models.Model):
    _name='pappaya.promotion'
    
    name = fields.Char('Description', readonly=True,size=100)
    pappaya_promotion_log = fields.One2many('pappaya.promotion.log', 'pappaya_promotion_id', 'Change Log', readonly=True)
    requested_by = fields.Many2one('hr.employee', 'Employee Name')
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type",related="requested_by.unit_type_id")
    category_id = fields.Many2one('pappaya.employee.category','Category',related='requested_by.category_id')
    sub_category_id = fields.Many2one('hr.employee.subcategory','Sub Category',related="requested_by.sub_category_id")
    
    requested_date = fields.Date('Date', default=fields.Date.today(), required=True, readonly=True, states={'draft': [('readonly', False)]})
    requester_comments = fields.Text('Requester Comments', readonly=True, states={'draft': [('readonly', False)]},size=300)
    approver_comments = fields.Text('Approver Comments',size=300)
    state = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved'),('rejected', 'Rejected'),('cancelled', 'Cancelled')], default='draft')
    emp_id = fields.Char(string='Employee ID', size=6)
    employee_id = fields.Char(string="Full Employee ID")
    
    source_dept = fields.Many2one('hr.department',string='Present Department')
    destination_dept = fields.Many2one('hr.department',string='Proposed Department',states={'draft': [('readonly', False)]})
    
    source_des = fields.Many2one('hr.job',string='Present Designation')
    destination_des = fields.Many2one('hr.job',string='Proposed Designation',states={'draft': [('readonly', False)]})

    contract_id = fields.Many2one('hr.contract',string="Contract")
    source_wage = fields.Integer(string='Present Wage')
    promote_wage = fields.Integer(string='Proposed Wage')
    
    subject_id = fields.Many2one('pappaya.subject', string='Subject')
    is_budget_applied = fields.Boolean(related='destination_des.is_budget_applicable',string='Is Budget Applied?')


    @api.onchange('destination_des')
    def _onchange_to_designation_id(self):
        for record in self:
            subjects = []
            if record.requested_by.branch_id:
                for lines in record.requested_by.branch_id.segment_cource_mapping_ids:
                    if lines.active and lines.segment_id.id == record.requested_by.segment_id.id:
                        subject_val = self.env['pappaya.subject'].search([('course_id', '=', lines.course_package_id.course_id.id)])
                        for subject in subject_val:
                            subjects.append(subject.id)
            return {'domain': {'subject_id': [('id', 'in', subjects)]}}

    @api.onchange('emp_id')
    def onchange_emp_id(self):
        for record in self:
            if record.emp_id:
                employee = self.env['hr.employee'].search([('emp_id', '=', record.emp_id), ('active', '=', True),('probation_state','=','pro_approve')])
                if employee:
                    record.requested_by     = employee.id
                    record.source_dept      = employee.department_id.id
                    record.source_des       = employee.job_id.id
                    record.destination_dept = employee.department_id.id
                else:
                    record.requested_by     = None
                    record.emp_id           = None

    @api.onchange('requested_by')
    def get_contract_by_employee(self):
        for record in self:
            department = []
            if record.requested_by:
                record.destination_dept = record.destination_des = None
                record.emp_id = record.requested_by.emp_id
                record.employee_id = record.requested_by.employee_id
                record.source_dept = record.requested_by.department_id.id
                record.source_des = record.requested_by.job_id.id
                record.destination_dept = record.requested_by.department_id.id
                if record.requested_by.branch_id :
                    current_contract = self.env['hr.contract'].search([('employee_id','=',record.requested_by.id),
                                                                   ('state','=','open')])
                    if current_contract:
                        record.contract_id = current_contract[0].id
                        record.source_wage = self.contract_id.wage
                        record.promote_wage = self.contract_id.wage
                    job_positions = self.env['hr.job'].search([('office_type_id', '=', record.requested_by.branch_id.office_type_id.id),
                                                                ('category_id', '=', record.requested_by.category_id.id),
                                                                ('sub_category_id', '=', record.requested_by.sub_category_id.id),
                                                                ('department_id', '=', record.destination_dept.id)])
                    for job in job_positions:
                        department.append(job.id)
                    # 'destination_dept': [('id', 'in', department)],
            return {'domain': {'contract_id': [('employee_id', '=', record.requested_by.id)],'destination_des': [('id', 'in', department)]}}
        
#     @api.onchange('destination_dept')
#     def onchange_branch_designation_id(self):
#         for record in self:
#             job_id = []
#             record.destination_des = None
#             if record.office_type_id and record.category_id and record.sub_category_id and record.department_id:
#                 job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),
#                                                            ('category_id', '=', record.category_id.id),
#                                                            ('sub_category_id', '=', record.sub_category_id.id),
#                                                            ('department_id', '=', record.destination_dept.id)
#                                                            ])
#                 for job in job_positions:
#                     job_id.append(job.id)
#             return {'domain': {'destination_des': [('id', 'in', job_id)]}}    
        


    @api.constrains('requested_date')
    def check_requested_date(self):
        for record in self:
            if record.requested_date:
                if datetime.strptime(record.requested_date, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
                    raise ValidationError('Please check future date not allowed')
            if record.requested_date and record.requested_by.date_of_joining:
                if record.requested_date < record.requested_by.date_of_joining:
                    doj = parser.parse(record.requested_by.date_of_joining)
                    proper_doj = doj.strftime('%d-%m-%Y')
                    raise ValidationError(_("Date is not Acceptable.\n It must be greater than Employee's Date of Joining %s ") % (proper_doj))


    @api.constrains('promote_wage')
    def check_promote_wage(self):
        for record in self:
            if record.destination_des.budgeted_salary and record.promote_wage and record.promote_wage > record.destination_des.budgeted_salary:
                raise ValidationError(_("Maximum acceptable Wage is Rs. %s") % (math.ceil(record.destination_des.budgeted_salary)))
            if record.promote_wage < 0:
                raise ValidationError(_("Proposed Wage should not be Negative"))

#     @api.onchange('destination_des')
#     def onchange_destination_des(self):
#         for record in self:
#             record.promote_wage = record.destination_des.budgeted_salary


    @api.model
    def create(self, vals):
        if 'requested_by' in vals and vals['requested_by']:
            vals['name'] = self.env['hr.employee'].browse(vals['requested_by']).name+' is requesting for employee promotion'
        return super(pappaya_promotion, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'requested_by' in vals and vals['requested_by']:
            vals['name'] = self.env['hr.employee'].browse(vals['requested_by']).name +' is requesting for employee promotion'
        res = super(pappaya_promotion, self).write(vals)
        return res
    
    @api.multi
    def button_request(self):
        for record in self:
            pappaya_promotion_log = [(0, 0, {
                'state_from': 'draft',
                'state_to': 'requested',
                'user_id': self.env.uid,
                'activity_time': datetime.now()
                })]
            wage = 0.0
            if record.promote_wage > 0:
                wage = record.promote_wage
            else:
                wage = record.source_wage

            if record.requested_by and record.destination_des.is_budget_applicable:
                budget_value = self.env['pappaya.budget.hr'].search([('branch_id', '=', record.requested_by.branch_id.id), ('segment_id', '=', record.requested_by.segment_id.id), \
                                                                    ('state', '=', 'confirm'), ('active', '=', True)], limit=1, order='id desc')
                if budget_value:
                    for budget_line in budget_value.budget_line_ids:
                        if budget_line.subject_id.id == record.subject_id.id:
                            if (budget_line.new_vacancy_count - budget_line.occupied_vacancies) > 0:
                                if budget_line.budget_available < wage:
                                    raise ValidationError(_("Proposed Wage exceeds the Available Budget Amount (Rs. %s)") % (math.ceil(budget_line.budget_available)))
                                if budget_line.avg_salary < wage:
                                    raise ValidationError(_("Proposed Wage should not be greater than Allotted Average Salary (Rs. %s)") % (math.ceil(budget_line.avg_salary)))

            record.write({'state': 'requested', 'pappaya_promotion_log': pappaya_promotion_log, 'promote_wage':wage})
            
    @api.multi
    def button_approve(self):
        for record in self:
            pappaya_promotion_log = [(0, 0, {
                'state_from': 'requested',
                'state_to': 'approved',
                'user_id': self.env.uid,
                'activity_time': datetime.now()
                })]
            wage = 0.0
            if record.promote_wage > 0:
                wage = record.promote_wage
            else:
                wage = record.source_wage

            if record.requested_by and record.destination_des.is_budget_applicable:
                budget_value = self.env['pappaya.budget.hr'].search([('branch_id', '=', record.requested_by.branch_id.id), ('segment_id', '=', record.requested_by.segment_id.id), \
                                                                    ('state', '=', 'confirm'), ('active', '=', True)], limit=1, order='id desc')
                if budget_value:
                    for budget_line in budget_value.budget_line_ids:
                        if budget_line.subject_id.id == record.subject_id.id:
                            if (budget_line.new_vacancy_count - budget_line.occupied_vacancies) > 0:
                                if budget_line.budget_available < wage:
                                    raise ValidationError(_("Proposed Wage exceeds the Available Budget Amount (Rs. %s)") % (math.ceil(budget_line.budget_available)))
                                if budget_line.avg_salary < wage:
                                    raise ValidationError(_("Proposed Wage should not be greater than Allotted Average Salary (Rs. %s)") % (math.ceil(budget_line.avg_salary)))

                                budget_line.budget_taken += record.requested_by.gross_salary
                                budget_line.occupied_vacancies += 1
                                employee_line = self.env['pappaya.budget.employee.line']
                                employee_line.create({
                                    'budget_id': budget_value.id,
                                    'employee_id': record.requested_by.id,
                                    'employee_wage': record.promote_wage,
                                    'origin_of_employee': 'From Employee Promotion',
                                })
                                budget_value.occupied_vacancies += 1
                            else:
                                raise ValidationError("There is no Vacancy available")

                else:
                    raise ValidationError("Budget is not incorporated ")

            record.requested_by.sudo().write({'department_id':record.destination_dept.id,'job_id':record.destination_des.id,'gross_salary':wage})
            if record.subject_id:
                record.requested_by.sudo().write({'subject_id':record.subject_id.id})
                
            current_contract = record.contract_id
            for contract in current_contract:
                contract.sudo().write({'department_id':record.destination_dept.id,'job_id':record.destination_des.id,'wage':wage or False})
            record.write({'state': 'approved', 'pappaya_promotion_log': pappaya_promotion_log})            
            
    @api.multi
    def button_reject(self):
        for record in self:
            pappaya_promotion_log = [(0, 0, {
                'state_from': 'requested',
                'state_to': 'rejected',
                'user_id': self.env.uid,
                'activity_time': datetime.now()
                })]
            record.write({'state': 'rejected', 'pappaya_promotion_log': pappaya_promotion_log})
            
    @api.multi
    def button_reset(self): 
        for record in self:
            pappaya_promotion_log = [(0, 0, {
                'state_from': record.state,
                'state_to': 'draft',
                'user_id': self.env.uid,
                'activity_time': datetime.now()
                })]
            record.write({'state': 'draft', 'pappaya_promotion_log': pappaya_promotion_log})        
        
    @api.multi
    def button_cancel(self):
        for record in self:
            pappaya_promotion_log = [(0, 0, {
                'state_from': record.state,
                'state_to': 'cancelled',
                'user_id': self.env.uid,
                'activity_time': datetime.now()
                })]
            record.write({'state': 'cancelled', 'pappaya_promotion_log': pappaya_promotion_log})           

class pappaya_promotion_log(models.Model):
    _name = 'pappaya.promotion.log'
    _rec_name = 'state_from'
    
    pappaya_promotion_id = fields.Many2one('pappaya.promotion', 'Employee Promotion')
    state_from = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved'),('rejected', 'Rejected'),('cancelled', 'Cancelled')])
    state_to = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved'),('rejected', 'Rejected'),('cancelled', 'Cancelled')])
    user_id = fields.Many2one('res.users', 'Changed By')
    activity_time = fields.Datetime('Changed On')


class HrEmployeeInheritPromotion(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_promotions(self):
        for record in self:
            record.promotions_count = record.env['pappaya.promotion'].sudo().search_count([('requested_by', '=', record.id)])

    promotions_count = fields.Integer(string="Promotions Count", compute='_compute_employee_promotions')
