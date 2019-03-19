# -*- coding: utf-8 -*-
from datetime import datetime,date
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import Warning
from odoo.exceptions import UserError, ValidationError
import math
from lxml import etree
from dateutil.relativedelta import relativedelta


class EmployeeTransfer(models.Model):
    _name = 'employee.transfer'
    _description = 'Employee Transfer'
    _order = "id desc"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _rec_name = 'employee_id'

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    name = fields.Char(string='Name', help='Give a name to the Transfer', copy=False, default="/", readonly=True)
    organization_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    transfer_number = fields.Char(string='Transfer No',size=100)
    type = fields.Selection([('internal','Internal'),('external','External')],string='Type',default='internal')
    emp_id = fields.Char('Employee ID', size=6)
    employee_id_all = fields.Char('Full Employee ID',track_visibility='onchange',size=100)
    employee_id = fields.Many2one('hr.employee', string='Employee', help='Select the employee you are going to transfer')
    date = fields.Date(string='Date', default=fields.Date.today())
    current_branch_id = fields.Many2one('operating.unit', 'From Branch',domain=[('type','=','branch')], copy=False,
                             help='The Branch/School which the employee is transferred')
    current_department_id = fields.Many2one('hr.department', string='Department')
    current_designation_id = fields.Many2one('hr.job', string='Designation')
    state = fields.Selection(
        [('draft', 'Draft'), ('cancel', 'Cancelled'), ('initiate', 'Transfer Initiate'), ('transfered', 'Transfered')],
        string='Status', readonly=True, copy=False, default='draft', track_visibility='onchange',
        help=" * The 'New' status is used when a transfer is created and unconfirmed Transfer.\n"
             " * The 'Transfer Initiate' status is used when the user initiate the transfer. It stays in the open status till the other branch/company receive the employee.\n"
             " * The 'Transfered' status is set automatically when the employee is Joined/Received.\n"
             " * The 'Cancelled' status is used when user cancel Transfer.")
    to_branch_id = fields.Many2one('operating.unit', 'To Branch',domain=[('type','=','branch')])
    
    to_branch_entity_id = fields.Many2one('operating.unit',string='Entity',related="current_branch_id.parent_id")
    to_branch_office_type = fields.Many2one('pappaya.office.type',string='Office Type',related="current_branch_id.office_type_id")
    to_department_id = fields.Many2one('hr.department', string='To Department')
    to_designation_id = fields.Many2one('hr.job', string='To Designation')
    
    
    
    note = fields.Text(string='Internal Notes' ,size=200)
    responsible = fields.Many2one('hr.employee', string='Responsible', default=_default_employee, readonly=True)
    
    subject_id = fields.Many2one('pappaya.subject', string='Subject')
    is_budget_applied = fields.Boolean(related='to_designation_id.is_budget_applicable',string='Is Budget Applied?')


    @api.onchange('to_designation_id')
    def _onchange_to_designation_id(self):
        for record in self:
            subjects = []
            if record.to_branch_id :
                for lines in record.to_branch_id.segment_cource_mapping_ids:
                    if lines.active and lines.segment_id.id == record.employee_id.segment_id.id:
                        subject_val = self.env['pappaya.subject'].search([('course_id', '=', lines.course_package_id.course_id.id)])
                        for subject in subject_val:
                            subjects.append(subject.id)
            return {'domain': {'subject_id': [('id', 'in', subjects)]}}

    @api.onchange('to_branch_id')
    def onchange_to_branch_id(self):
        for record in self:
            department = []
            if record.to_branch_id:
#                 record.to_branch_entity_id = record.to_branch_id.parent_id.id
#                 record.to_branch_office_type = record.to_branch_id.office_type_id.id
                record.to_department_id = record.to_designation_id = None
                job_positions = self.env['hr.job'].search([('office_type_id', '=', self.to_branch_office_type.id),
                                                           ('category_id', '=', record.employee_id.category_id.id),
                                                           ('sub_category_id', '=', record.employee_id.sub_category_id.id)])
                for job in job_positions:
                    department.append(job.department_id.id)
            return {'domain': {'to_department_id': [('id', 'in', department)]}}

    @api.constrains('date')
    def check_date(self):
        for record in self:
            if datetime.strptime(record.date, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
                raise ValidationError('Please check the date, Future date not allowed')
            if datetime.strptime(record.date, DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
                raise ValidationError('Please check the date, Past date not allowed')
            
    # @api.constrains('type','to_department_id','to_designation_id')
    # def same_transfer_constrains(self):
    #     for record in self:
    #         if record.type == 'internal':
    #             if record.current_department_id.id == record.to_department_id.id and record.current_designation_id.id == record.to_designation_id.id:
    #                 raise ValidationError(_("Please enter different To Department or To Designation"))
    #         else:
    #               if record.current_branch_id.id == record.to_branch_id.id and record.current_department_id.id == record.to_department_id.id and record.current_designation_id.id == record.to_designation_id.id:
    #                 raise ValidationError(_("Please enter different To Branch or To Department or To Designation"))
    
    @api.onchange('emp_id')
    def onchange_emp_id(self):
        for record in self:
            if record.emp_id:
                employee = self.env['hr.employee'].search([('emp_id','=',record.emp_id),('active','=',True)])
                if employee:
                    record.employee_id = employee.id
                    record.employee_id_all = employee.employee_id
                else:
                    record.employee_id = None

    @api.onchange('to_branch_office_type')
    def onchange_to_branch_office_type(self):
        department = []
        self.to_department_id = None
        job_positions = self.env['hr.job'].search([('office_type_id', '=', self.employee_id.unit_type_id.id),
                                                   ('category_id', '=', self.employee_id.category_id.id),
                                                   ('sub_category_id', '=', self.employee_id.sub_category_id.id),
                                                   ])
        for job in job_positions:
            department.append(job.department_id.id)
        return {'domain': {'to_department_id': [('id', 'in', department)]}}

    @api.onchange('to_department_id','type')
    def onchange_to_department_id(self):
        job_id = []
        if self.to_department_id and self.type:
            self.to_designation_id = None
            job_positions = self.env['hr.job'].search([('office_type_id', '=', self.employee_id.unit_type_id.id),
                                                       ('category_id', '=', self.employee_id.category_id.id),
                                                       ('sub_category_id', '=', self.employee_id.sub_category_id.id),
                                                       ('department_id', '=', self.to_department_id.id)
                                                       ])
            for job in job_positions:
                job_id.append(job.id)
        return {'domain': {'to_designation_id': [('id', 'in', job_id)]}}
        

    @api.onchange('employee_id','type')
    def onchange_employee_id(self):
        for record in self:
            record.to_department_id = record.to_designation_id = None
            if record.employee_id:
                record.employee_id_all = record.employee_id.employee_id
                record.current_branch_id = record.employee_id.branch_id.id
                record.current_department_id = record.employee_id.department_id.id
                record.current_designation_id = record.employee_id.job_id.id
                record.emp_id = record.employee_id.emp_id
                if record.type == 'internal':
                    record.to_branch_id = record.current_branch_id.id
                    record.to_branch_entity_id = record.current_branch_id.parent_id.id
                    record.name = "Internal Transfer Of " + record.employee_id.name + ' - ' +record.emp_id
                    # return {'domain': {'to_department_id': [('company_id', '=', record.current_branch_id.id)]}}
                else:
                    record.to_branch_id = None
                    record.to_branch_entity_id = record.current_branch_id.parent_id.id
                    record.name = "External Transfer Of " + record.employee_id.name + ' - ' +record.emp_id
                    # return {'domain': {'to_department_id': [('company_id', '=', record.to_branch_id.id)]}}
            else:
                record.current_branch_id = record.current_department_id = record.current_designation_id = record.name = record.emp_id = None
                

    @api.multi
    def init_transfer(self):
        for record in self:
            if record.to_branch_id and record.to_designation_id.is_budget_applicable:
                budget_value = self.env['pappaya.budget.hr'].search([('branch_id', '=', record.to_branch_id.id), ('segment_id', '=', record.employee_id.segment_id.id), \
                                                                    ('state', '=', 'confirm'), ('active', '=', True)], limit=1, order='id desc')
                if budget_value:
                    for budget_line in budget_value.budget_line_ids:
                        if budget_line.subject_id.id == record.subject_id.id:
                            if (budget_line.new_vacancy_count - budget_line.occupied_vacancies) > 0:
                                if budget_line.avg_salary < record.employee_id.gross_salary:
                                    raise ValidationError(_("Gross salary should not be greater than Allotted Average Salary (Rs. %s)") % (math.ceil(budget_line.avg_salary)))
                                if budget_line.budget_available < record.employee_id.gross_salary:
                                    raise ValidationError(_("Gross salary exceeds the Available Budget Amount (Rs. %s)") % (math.ceil(budget_line.budget_available)))
                            else:
                                raise ValidationError("There is no Vacancy available")

                else:
                    raise ValidationError("Budget is not Created/Available ")

            mail_mail = self.env['mail.mail']
            users = record.env['res.users'].search(['|', ('hr_operations_head', '=', True), ('hr_cpo', '=', True)])
            # users = record.env['res.users'].search([('id', '=', 29)])
            email_from = ''
            outgoing_email = self.env['ir.mail_server'].search([('id', '=', 1)])
            if outgoing_email:
                email_from = outgoing_email.smtp_user
            for user in users:
                try:
                    if user.email:
                        email_to = user.email
                        email_from = email_from
                        subject = "Employee Transfer Initiated"
                        body = _("Hi,<br/>")
                        body += _("<br/><p> <b> Dear %s,</b> </p> </br> <p> %s - %s Initiated Transfer From %s - %s - %s To %s - %s - %s </p> </br>"
                                  %(user.employee_id.name, record.employee_id.name, record.emp_id, record.current_branch_id.name, record.current_department_id.name, record.current_designation_id.name, \
                                    record.to_branch_id.name, record.to_department_id.name, record.to_designation_id.name))
                        footer="With Regards,<br/>HR<br/>"
                        mail = mail_mail.create({
                            'email_to': email_to,
                            'email_from': email_from,
                            'res_id':user[0],
                            'record_name':'Employee Transfer Initiated',
                            'subject': subject,
                            'body_html':'''<span  style="font-size:14px"><br/>
                            <br/>%s<br/>
                            <br/>%s</span>''' %(body,footer),
                            })
                        mail.send(mail)
                        mail.mail_message_id.write({'res_id':user[0]})
                except :
                    print ("Exception")

            record.state = 'initiate'


    @api.multi
    def approve_transfer(self):
        for record in self:

            if record.to_branch_id and record.to_designation_id.is_budget_applicable:
                budget_value = self.env['pappaya.budget.hr'].search([('branch_id', '=', record.to_branch_id.id), ('segment_id', '=', record.employee_id.segment_id.id), \
                                                                    ('state', '=', 'confirm'), ('active', '=', True)], limit=1, order='id desc')
                if budget_value:
                    for budget_line in budget_value.budget_line_ids:
                        if budget_line.subject_id.id == record.subject_id.id:
                            if (budget_line.new_vacancy_count - budget_line.occupied_vacancies) > 0:
                                if budget_line.avg_salary < record.employee_id.gross_salary:
                                    raise ValidationError(_("Gross salary should not be greater than Allotted Average Salary (Rs. %s)") % (math.ceil(budget_line.avg_salary)))
                                if budget_line.budget_available < record.employee_id.gross_salary:
                                    raise ValidationError(_("Gross salary exceeds the Available Budget Amount (Rs. %s)") % (math.ceil(budget_line.budget_available)))

                                budget_line.budget_taken += record.employee_id.gross_salary
                                budget_line.occupied_vacancies += 1
                                employee_line = self.env['pappaya.budget.employee.line']
                                employee_line.sudo().create({
                                    'budget_id': budget_value.id,
                                    'employee_id': record.employee_id.id,
                                    'employee_wage': record.employee_id.gross_salary,
                                    'origin_of_employee': 'From Employee Transfer',
                                })
                                budget_value.occupied_vacancies += 1
                            else:
                                raise ValidationError("There is no Vacancy available")

                else:
                    raise ValidationError("Budget is not incorporated ")

            contract = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id),('state','=','open')], limit=1, order='id desc')
            for obj_contract in contract:
                record.employee_id.sudo().write({
                    'branch_id': record.to_branch_id.id,
                    'department_id': record.to_department_id.id,
                    'job_id': record.to_designation_id.id,
                    'category_id':record.to_designation_id.category_id.id,
                    'sub_category_id':record.to_designation_id.sub_category_id.id,
                    'subject_id':record.subject_id.id,
                })
                if record.subject_id:
                    record.employee_id.sudo().write({'subject_id':record.subject_id.id})
                record.employee_id_all = record.employee_id.employee_id
                obj_contract.sudo().write({
                    'department_id' : record.to_department_id.id,
                    'job_id' : record.to_designation_id.id
                })

            if not record.transfer_number:
                record.transfer_number = self.env['ir.sequence'].next_by_code('pappaya.employee.transfer') or _('New')

            mail_mail = self.env['mail.mail']
            users = record.env['res.users'].search(['|', ('hr_operations_head', '=', True), ('hr_cpo', '=', True)])
            # users = record.env['res.users'].search([('id', '=', 29)])
            email_from = ''
            outgoing_email = self.env['ir.mail_server'].search([('id', '=', 1)])
            if outgoing_email:
                email_from = outgoing_email.smtp_user
            for user in users:
                try:
                    if user.email:
                        email_to = user.email
                        email_from = email_from
                        subject = "Employee Transfer Approved"
                        body = _("Hi,<br/>")
                        body += _("<br/><p> <b> Dear %s,</b> </p> </br> <p> %s - %s Approved Transfer From %s - %s - %s To %s - %s - %s </p> </br>"
                                    % (user.employee_id.name, record.employee_id.name, record.emp_id, record.current_branch_id.name, \
                                    record.current_department_id.name, record.current_designation_id.name, \
                                    record.to_branch_id.name, record.to_department_id.name, record.to_designation_id.name))
                        footer = "With Regards,<br/>HR<br/>"
                        mail = mail_mail.create({
                            'email_to': email_to,
                            'email_from': email_from,
                            'res_id': user[0],
                            'record_name': 'Employee Transfer Approved',
                            'subject': subject,
                            'body_html': '''<span  style="font-size:14px"><br/>
                                        <br/>%s<br/>
                                        <br/>%s</span>''' % (body, footer),
                        })
                        mail.send(mail)
                        mail.mail_message_id.write({'res_id': user[0]})
                except:
                    print("Exception")

            record.state = 'transfered'
            # if contract.ids == []:
            #     raise ValidationError("There's no Running Contract for the Employee.")

    
    @api.multi
    def cancel_transfer(self):
        for record in self:
            record.state = 'cancel'

#     @api.model
#     def create(self, vals):
#         vals['name'] = "Transfer Of " + self.env['hr.employee'].browse(vals['employee_id']).name
#         res = super(EmployeeTransfer, self).create(vals)
#         return res
# 
#     @api.multi
#     def write(self, vals):
#         if 'employee_id' in vals:
#             vals['name'] = "Transfer Of " + self.env['hr.employee'].browse(vals['employee_id']).name
#         res = super(EmployeeTransfer, self).write(vals)
#         return res

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise ValidationError("Sorry, You are not allowed to delete it. Records which is in 'Draft' state only be deleted")
        return super(EmployeeTransfer, self).unlink()


class HrEmployeeInheritTransfer(models.Model):
    _inherit = "hr.employee"

    @api.one
    def _compute_employee_transfers(self):
        for record in self:
            record.transfers_count = record.env['employee.transfer'].search_count([('employee_id', '=', record.id)])

    transfers_count = fields.Integer(string="Transfers Count", compute='_compute_employee_transfers')
