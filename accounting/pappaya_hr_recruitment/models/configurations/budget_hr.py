# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import math

class PappayaHRBudget(models.Model):
    _name = "pappaya.budget.hr"
    _rec_name = "branch_id"


    @api.depends('budget_line_ids', 'previous_budget_remain')
    def get_total_budget(self):
        for record in self:
            value = 0
            for line in record.budget_line_ids:
                value += line.budget_for_vacancy
            record.total_budget = math.ceil(value + record.previous_budget_remain)

    @api.depends('total_budget', 'employee_line_ids')
    def get_budget_inhand(self):
        for record in self:
            value = 0
            for line in record.employee_line_ids:
                value += line.employee_wage
            if record.total_budget:
                record.budget_inhand = math.ceil(record.total_budget - value)

    @api.onchange('branch_id','program_id','segment_id')
    def onchange_branch_segment(self):
        for record in self:
            if record.branch_id and record.program_id and record.segment_id:
                budget_value = self.env['pappaya.budget.hr'].search([('branch_id', '=', record.branch_id.id), ('program_id', '=', record.program_id.id),
                                                                    ('segment_id', '=', record.segment_id.id), ('state', '=', 'confirm'), ('active', '=', True)
                                                                    ], limit=1, order='id desc')
                record.previous_budget_remain = math.ceil(budget_value.budget_inhand)
                record.previous_budget_id = budget_value.id
                if record.previous_budget_id:
                    record.previous_budget_id.active = False

    # def _default_previous_budget_remain(self):
    #     for record in self:
    #         budget_value = self.env['pappaya.budget.hr'].search(
    #             [('branch_id', '=', record.branch_id.id), ('program_id', '=', record.program_id.id),
    #              ('segment_id', '=', record.segment_id.id), ('state', '=', 'confirm'), ('active', '=', True)
    #              ], limit=1, order='id desc')
    #         record.previous_budget_remain = math.ceil(budget_value.budget_inhand)
    #         record.previous_budget_id = budget_value.id

    name = fields.Char(string='Subject',size=50)
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    fiscal_year_id = fields.Many2one('fiscal.year', 'Fiscal Year', default=lambda self: self.env['fiscal.year'].search([('active', '=', True)]))
    state_id = fields.Many2one('res.country.state', 'State', compute='_get_state_program_segment', store=True)
    program_id = fields.Many2one('pappaya.programme', 'Programme')
    segment_id = fields.Many2one('pappaya.segment', 'Segment')
    budget_line_ids = fields.One2many('pappaya.budget.hr.line', 'budget_id', 'Budget Lines')
    employee_line_ids = fields.One2many('pappaya.budget.employee.line', 'budget_id', 'Employees')
    active = fields.Boolean(string='Is Active', default=True)

    balance_vacancies = fields.Integer('Balance Vacancies', compute='get_balance_vacancies', store=True)
    occupied_vacancies = fields.Integer('Occupied Vacancies')
    total_vacancies = fields.Integer('Total Vacancies', compute='get_total_vacancies', store=True)
    # avg_salary = fields.Integer('Average Salary', compute='get_avg_salary', store=True)
    state = fields.Selection([('draft', 'Draft'),('cancel', 'Cancelled'),('confirm', 'Approved'),
        ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

    budget_inhand = fields.Integer('Budget in Hand', compute='get_budget_inhand', store=True)
    total_budget = fields.Integer('Total Budget', compute='get_total_budget', store=True)
    previous_budget_remain = fields.Integer('Budget from Previous Record')
    previous_budget_id = fields.Many2one('pappaya.budget.hr',string='Previous Budget')
    details_get_button = fields.Boolean('Get Details')

    # @api.model
    # def fields_get(self, allfields=None, attributes=None):
    #     fields_to_hide = ['branch_id','state_id']
    #     res = super(PappayaHRBudget, self).fields_get(allfields, attributes=attributes)
    #     for field in fields_to_hide:
    #         res[field]['selectable'] = False
    #     return res

    @api.multi
    def budget_confirm(self):
        for record in self:
            record.write({'state':'confirm'})
            if record.previous_budget_id:
                record.previous_budget_id.active = False

    @api.multi
    def budget_cancel(self):
        for record in self:
            record.write({'state':'cancel', 'active':False})

    @api.constrains('branch_id', 'program_id', 'segment_id')
    def check_existing_record(self):
        for record in self:
            if record.branch_id and record.program_id and record.segment_id:
                budget = record.env['pappaya.budget.hr'].search([('branch_id', '=', record.branch_id.id), ('program_id', '=', record.program_id.id),
                     ('segment_id', '=', record.segment_id.id), ('state', 'not in', ('confirm','cancel'))])
                if len(budget) > 1:
                    raise ValidationError(_("Already one Budget was created for this conditions"))

    # @api.constrains('branch_id', 'program_id', 'segment_id', 'state', 'active')
    # def check_branch_program_segment_id(self):
    #     if len(self.search([('branch_id', '=', self.branch_id.id), ('program_id', '=', self.program_id.id),('segment_id', '=', self.segment_id.id), \
    #                         ('fiscal_year_id', '=', self.fiscal_year_id.id), ('state', '=', 'confirm'), ('active', '=', True)])) > 1:
    #         raise ValidationError("Record already exists for this Fiscal Year")

    @api.depends('budget_line_ids')
    def get_total_vacancies(self):
        for record in self:
            value = 0
            for line in record.budget_line_ids:
                value += line.new_vacancy_count
            record.total_vacancies = value

    # @api.depends('budget_line_ids')
    # def get_avg_salary(self):
    #     for record in self:
    #         amount_value = 0
    #         count_value = 0
    #         for line in record.budget_line_ids:
    #             amount_value += line.budget_for_vacancy
    #             count_value += line.new_vacancy_count
    #         if count_value and  amount_value:
    #             record.avg_salary = math.ceil(amount_value/count_value)

    @api.depends('occupied_vacancies','total_vacancies')
    def get_balance_vacancies(self):
        for record in self:
            record.balance_vacancies = record.total_vacancies - record.occupied_vacancies

    @api.depends('branch_id')
    def _get_state_program_segment(self):
        for record in self:
            record.state_id = record.branch_id.state_id

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        for record in self:
            self.program_id = self.segment_id = None
            segment_ids = program_ids = []
            for lines in record.branch_id.segment_cource_mapping_ids:
                if lines.fiscal_year_id.id == record.fiscal_year_id.id and lines.active:
                    segment_ids.append(lines.segment_id.id)
                    program_ids.append(lines.programme_id.id)
            return {'domain': {'program_id': [('id', 'in', program_ids)],'segment_id': [('id', 'in', segment_ids)]}}

    @api.model
    def create(self, vals):
        # subject_val = self.env['pappaya.budget.hr'].search([('branch_id', '=', vals['branch_id']),
        #                                                                ('program_id', '=', vals['program_id']),
        #                                                                ('segment_id', '=', vals['segment_id']),
        #                                                                ('fiscal_year_id', '=',vals['fiscal_year_id']),
        #                                                                ('state', '=', 'confirm'),
        #                                                                ('active', '=', True)
        #                                                                ])
        # if subject_val.ids != []:
        #     raise ValidationError('Record already exists for this Fiscal Year')
        # else:
        res = super(PappayaHRBudget, self).create(vals)
        return res

    @api.multi
    @api.onchange('details_get_button')
    def onchange_details_get_button(self):
        if self.budget_line_ids.ids == []:
            if self.branch_id and self.state_id and self.program_id and self.segment_id and self.fiscal_year_id:

                work_subject = self.env['pappaya.work.hours.subject'].search([('state_id', '=', self.state_id.id), ('program_id', '=', self.program_id.id),
                     ('segment_id', '=', self.segment_id.id), ('fiscal_year_id', '=', self.fiscal_year_id.id),('active', '=', True)])

                number_subject = self.env['pappaya.number.hours.subject'].search([('state_id', '=', self.state_id.id), ('program_id', '=', self.program_id.id),
                     ('segment_id', '=', self.segment_id.id), ('fiscal_year_id', '=', self.fiscal_year_id.id),('active', '=', True)])

                section_students = self.env['pappaya.number.students'].search([('branch_id', '=', self.branch_id.id), ('program_id', '=', self.program_id.id),
                     ('segment_id', '=', self.segment_id.id), ('fiscal_year_id', '=', self.fiscal_year_id.id),('active', '=', True)])

                if work_subject.ids == []:
                    raise ValidationError('First Process the Workload Hours for this Fiscal Year')

                if number_subject.ids == []:
                    raise ValidationError('First Process the Number of Hours for this Fiscal Year')

                if section_students.ids == []:
                    raise ValidationError('First Process the Number of Students for this Fiscal Year')

                for work in work_subject:
                    for work_line in work.subject_line_ids:
                        no_hours = 0
                        for number in number_subject.subject_line_ids:
                            if work_line.subject_id == number.subject_id:
                                no_hours += number.number_hours

                        work_line.sudo().write({'number_hours':no_hours})

                branch_val = self.env['operating.unit'].search([('id', '=', self.branch_id.id)])

                subject_value = []
                budget_lines = []
                for value in branch_val.segment_cource_mapping_ids:
                    if value.fiscal_year_id == self.fiscal_year_id and value.segment_id == self.segment_id and value.programme_id == self.program_id:
                        for course in value.course_package_id:
                            subject_val = self.env['pappaya.subject'].search([('course_id', '=', course.course_id.id)])
                            for subject in subject_val:
                                # if subject:
                                if subject and subject.id not in subject_value:
                                    subject_value.append(subject.id)
                                    hours_total = workload_total = section_total = 0

                                    hours_subject = self.env['pappaya.work.hours.subject'].search([('state_id', '=', self.state_id.id), ('program_id', '=', self.program_id.id),
                                         ('segment_id', '=', self.segment_id.id),('fiscal_year_id', '=', self.fiscal_year_id.id), ('active', '=', True)])

                                    for hour_line in hours_subject.subject_line_ids:
                                        if subject.id == hour_line.subject_id.id:
                                            hours_total += hour_line.number_hours
                                            workload_total += hour_line.workload_hours

                                    section_students = self.env['pappaya.number.students'].search([('branch_id', '=', self.branch_id.id), ('program_id', '=', self.program_id.id),
                                         ('segment_id', '=', self.segment_id.id),('fiscal_year_id', '=', self.fiscal_year_id.id), ('active', '=', True)])

                                    for section_line in section_students.student_line_ids:
                                        if course.course_id.id == section_line.class_id.id:
                                            section_total += section_line.number_sections

                                    staff_required = 0
                                    if section_total and hours_total and workload_total > 0:
                                        staff_required = math.ceil((section_total * hours_total) / workload_total)

                                    if self.branch_id and self.program_id and self.segment_id:
                                        previous_budget_id = self.env['pappaya.budget.hr'].search([('branch_id', '=', self.branch_id.id),
                                             ('program_id', '=', self.program_id.id),('segment_id', '=', self.segment_id.id), ('state', '=', 'confirm'),
                                             ('active', '=', True)], limit=1, order='id desc')

                                        if previous_budget_id:
                                            for line in previous_budget_id.budget_line_ids:
                                                if line.class_id and line.subject_id:
                                                    if line.class_id == course.course_id and line.subject_id == subject:
                                                        budget_lines.append((0, 0, {
                                                            'budget_id': self.id,
                                                            'class_id': course.course_id.id,
                                                            'subject_id': subject.id,
                                                            'staff_required_count': staff_required,
                                                            'previous_budget_remain': line.budget_available,
                                                            'existing_staff_count': (line.existing_staff_count + line.occupied_vacancies),
                                                            'avg_salary': line.avg_salary,
                                                        }))
                                        else:
                                            budget_lines.append((0, 0, {
                                                'budget_id': self.id,
                                                'class_id': course.course_id.id,
                                                'subject_id': subject.id,
                                                'staff_required_count': staff_required,
                                            }))

                self.budget_line_ids = budget_lines
                if self.previous_budget_id:
                    self.previous_budget_id.active = False


    # def get_subject_details(self):
    #     if self.budget_line_ids.ids == []:
    #
    #         hours_subject = self.env['pappaya.number.hours.subject'].search([('state_id', '=', self.state_id.id), ('program_id', '=', self.program_id.id),
    #              ('segment_id', '=', self.segment_id.id), ('fiscal_year_id', '=', self.fiscal_year_id.id),('active', '=', True)])
    #
    #         section_students = self.env['pappaya.number.students'].search([('branch_id', '=', self.branch_id.id), ('program_id', '=', self.program_id.id),
    #              ('segment_id', '=', self.segment_id.id), ('fiscal_year_id', '=', self.fiscal_year_id.id),('active', '=', True)])
    #
    #         if hours_subject.ids == []:
    #             raise ValidationError('First Process the Workload Subject Hours for this Fiscal Year')
    #
    #         if section_students.ids == []:
    #             raise ValidationError('First Process the Number of Students for this Fiscal Year')
    #
    #         branch_val = self.env['operating.unit'].search([('id', '=', self.branch_id.id)])
    #
    #         subject_value = []
    #         for value in branch_val.segment_cource_mapping_ids:
    #             if value.fiscal_year_id == self.fiscal_year_id and value.segment_id == self.segment_id and value.programme_id == self.program_id:
    #                 for course in value.course_package_ids:
    #                     subject_val = self.env['pappaya.subject'].search([('course_id', '=', course.course_id.id)])
    #                     for subject in subject_val:
    #                         if subject and subject.id not in subject_value:
    #                             subject_value.append(subject.id)
    #                             hours_total = 0
    #                             workload_total = 0
    #                             section_total = 0
    #
    #                             hours_subject = self.env['pappaya.number.hours.subject'].search([('state_id', '=', self.state_id.id), ('program_id', '=', self.program_id.id), ('segment_id', '=', self.segment_id.id), ('fiscal_year_id', '=', self.fiscal_year_id.id), ('active','=',True)])
    #                             for hour_line in hours_subject.subject_line_ids:
    #                                 if subject.id == hour_line.subject_id.id:
    #                                     hours_total += hour_line.number_hours
    #                                     workload_total += hour_line.workload_hours
    #
    #                             section_students = self.env['pappaya.number.students'].search([('branch_id', '=', self.branch_id.id), ('program_id', '=', self.program_id.id), ('segment_id', '=', self.segment_id.id), ('fiscal_year_id', '=', self.fiscal_year_id.id), ('active','=',True)])
    #                             for section_line in section_students.student_line_ids:
    #                                 if course.course_id.id == section_line.class_id.id:
    #                                     section_total += section_line.number_sections
    #
    #                             # if workload_total == 0:
    #                             #     raise ValidationError('First Process the Workload Hours for this Fiscal Year')
    #                             # if hours_total == 0:
    #                             #     raise ValidationError('First Process the Hours/Week for this Fiscal Year')
    #                             # if section_total == 0:
    #                             #     raise ValidationError('First Process the Section Count for this Fiscal Year')
    #
    #                             staff_required = 0
    #                             if section_total and hours_total and workload_total > 0:
    #                                 staff_required = math.ceil((section_total*hours_total)/workload_total)
    #
    #                             budget_line = self.env['pappaya.budget.hr.line']
    #                             res = budget_line.create({
    #                                 'budget_id': self.id,
    #                                 'class_id': course.course_id.id,
    #                                 'subject_id': subject.id,
    #                                 'staff_required_count': staff_required,
    #                             })
    #
    #                             if self.branch_id and self.program_id and self.segment_id:
    #                                 previous_budget_id = self.env['pappaya.budget.hr'].search([('branch_id', '=', self.branch_id.id),('program_id', '=', self.program_id.id),\
    #                                                                                         ('segment_id', '=', self.segment_id.id), ('state', '=', 'confirm'),('active', '=', True)], limit=1, order='id desc')
    #
    #                                 if previous_budget_id:
    #                                     for line in previous_budget_id.budget_line_ids:
    #                                         if line.class_id and line.subject_id:
    #                                             if line.class_id == res.class_id and line.subject_id == res.subject_id:
    #                                                 res.write({
    #                                                     'previous_budget_remain': line.budget_available,
    #                                                     'existing_staff_count': (line.existing_staff_count + line.occupied_vacancies),
    #                                                     'avg_salary': line.avg_salary,
    #                                                 })
    #
    #         if self.previous_budget_id:
    #             self.previous_budget_id.active = False
    #     return


class PappayaHRBudgetLine(models.Model):
    _name = "pappaya.budget.hr.line"

    @api.depends('staff_required_count', 'existing_staff_count')
    def _get_new_vacancy_count(self):
        for record in self:
            count = record.staff_required_count - record.existing_staff_count
            if count < 0:
                record.new_vacancy_count = 0
                record.budget_available = 0
            else:
                record.new_vacancy_count = count

    @api.depends('new_vacancy_count', 'avg_salary')
    def _get_required_budget(self):
        for record in self:
            if record.avg_salary > 0 and record.new_vacancy_count > 0:
                record.required_budget = math.ceil(record.new_vacancy_count * record.avg_salary)

    @api.depends('budget_for_vacancy', 'budget_taken','previous_budget_remain')
    def _get_budget_available(self):
        for record in self:
            if record.budget_for_vacancy or record.previous_budget_remain:
                record.budget_available = math.ceil(record.previous_budget_remain + record.budget_for_vacancy - record.budget_taken)
                if record.budget_available < 0:
                    record.budget_available = 0
            else:
                record.budget_available = 0


    @api.constrains('existing_staff_count','staff_required_count','avg_salary', 'required_budget', 'previous_budget_remain', 'budget_for_vacancy')
    def check_existing_staff_count(self):
        for record in self:
            if record.existing_staff_count:
                if record.existing_staff_count < 0:
                    raise ValidationError('Existing Staff Count should not be Negative')
            if record.staff_required_count:
                if record.staff_required_count < 0:
                    raise ValidationError('Required Staff Count should not be Negative')
            if record.new_vacancy_count < 0:
                raise ValidationError('No. of New Vacancies must be greater than Zero')
            if record.new_vacancy_count > 0 and record.avg_salary <= 0:
                raise ValidationError('Average Salary must be greater than Zero')
            if record.budget_for_vacancy < 0:
                raise ValidationError('Allotted Budget must be greater than Zero')
            if record.required_budget:
                if record.required_budget > math.ceil(record.budget_for_vacancy + record.previous_budget_remain):
                    raise ValidationError(_('Not enough Budget for the Subject %s ') % record.subject_id.name)
                # if record.required_budget > record.budget_for_vacancy:
                #     raise ValidationError(_('Not enough Budget for the Subject %s ') % record.subject_id.name)


    budget_id = fields.Many2one('pappaya.budget.hr', string='Budget ID')
    class_id = fields.Many2one('pappaya.course', string='Course')
    subject_id = fields.Many2one('pappaya.subject', string='Subject/Designation')
    # job_id = fields.Many2one('hr.job', string="Job Position")
    staff_required_count = fields.Integer('Total Staffs Required')
    existing_staff_count = fields.Integer('No. of Existing Staff')
    new_vacancy_count = fields.Integer('No. of New Vacancies', compute='_get_new_vacancy_count', store=True)
    avg_salary = fields.Integer('Average Salary')
    required_budget = fields.Integer('Required Budget', compute='_get_required_budget', store=True)
    budget_for_vacancy = fields.Integer('Allotted Budget')
    budget_taken = fields.Integer('Budget Taken')
    budget_available = fields.Integer('Available Budget', compute='_get_budget_available', store=True)
    occupied_vacancies = fields.Integer('Occupied Vacancies')
    previous_budget_remain = fields.Integer('Budget from Previous Record')


class PappayaHREmployeeLine(models.Model):
    _name = 'pappaya.budget.employee.line'

    budget_id = fields.Many2one('pappaya.budget.hr', string='Budget ID')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_wage = fields.Integer('Gross Salary PM')
    origin_of_employee = fields.Char('Status')
