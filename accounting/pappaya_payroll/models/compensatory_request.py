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


class PappayaCompensatoryRequest(models.Model):
    _name='leave.compensatory.request'
    _rec_name = 'employee_id'
    

    employee_id = fields.Many2one('hr.employee', 'Employee Name', required=True)
    emp_id = fields.Char(string='Employee ID', size=6)
    requested_date = fields.Date('Requested Date', default=fields.Date.today())
    state = fields.Selection([('draft', 'Draft'), ('requested', 'Requested'),('approved', 'Approved'), \
                              ('rejected', 'Rejected'),('cancelled', 'Cancelled')], default='draft', string='Status')
    work_date = fields.Date('Work Date')
    compoff_date = fields.Date('C-Off Date')
    date_from = fields.Date(string='From date')
    date_to = fields.Date(string='To date')
    branch_id = fields.Many2one('operating.unit', string='Branch')
    department_id = fields.Many2one('hr.department', string='Department')
    leave_type_id = fields.Many2one('hr.holidays.status', string='Leave Type')
    leave_type_value = fields.Char('Leave Type')
    year_of_passing = fields.Selection([(num, str(num)) for num in range(((datetime.now().year)), ((datetime.now().year) + 2))], 'Year')
    daily_attendance_line = fields.Many2many('hr.daily.attendance.line', string='Manual Attendance Line')

    @api.onchange('leave_type_id')
    def onchange_leave_type_id(self):
        for record in self:
            if record.leave_type_id:
                record.leave_type_value = record.leave_type_id.code
            record.date_from = record.date_to = record.work_date = record.compoff_date = None

    @api.constrains('date_from', 'date_to')
    def _check_validity_date_from_to(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError(_('"End Date" cannot be earlier than "Start Date".'))

    @api.model
    def create(self, vals):
        vals['requested_date'] = datetime.now().strftime("%Y-%m-%d")
        res = super(PappayaCompensatoryRequest, self).create(vals)
        return res

    @api.onchange('emp_id')
    def onchange_emp_id(self):
        for record in self:
            if record.emp_id:
                record.employee_id = record.branch_id = record.department_id = record.leave_type_id = None
                employee = self.env['hr.employee'].search([('emp_id', '=', record.emp_id), ('active', '=', True)])
                leave_ids = []
                if employee:
                    record.employee_id = employee.id
                    record.branch_id = employee.branch_id.id
                    record.department_id = employee.department_id.id
                    if employee.gender_id.name == 'Female':
                        if employee.marital != 'single':
                            leave_ids = self.env['hr.holidays.status'].search([('entity_id','=',employee.entity_id.id),
                                                                               ('office_type_id','=',employee.unit_type_id.id),
                                                                               ('code','in',['MTL','C-Off'])]).ids
                    else:
                        leave_ids = self.env['hr.holidays.status'].search([('entity_id','=',employee.entity_id.id),
                                                                           ('office_type_id','=',employee.unit_type_id.id),
                                                                           ('code','=','C-Off')]).ids
                return {'domain': {'leave_type_id':[('id','in',leave_ids)] }}

    @api.onchange('employee_id')
    def onchange_employee_id_value(self):
        for record in self:
            record.emp_id = record.branch_id = record.department_id = record.leave_type_id = None
            leave_ids = []
            if record.employee_id:
                record.emp_id = record.employee_id.emp_id
                record.branch_id = record.employee_id.branch_id.id
                record.department_id = record.employee_id.department_id.id
                if record.employee_id.gender_id.name == 'Female':
                        if record.employee_id.marital != 'single':
                            leave_ids = self.env['hr.holidays.status'].search([('entity_id','=',record.employee_id.entity_id.id),
                                                                               ('office_type_id','=',record.employee_id.unit_type_id.id),
                                                                               ('code','in',['MTL','C-Off'])]).ids
                        else:
                            leave_ids = self.env['hr.holidays.status'].search([('entity_id','=',record.employee_id.entity_id.id),
                                                                               ('office_type_id','=',record.employee_id.unit_type_id.id),
                                                                               ('code','=','C-Off')]).ids
            return {'domain': {'leave_type_id':[('id','in',leave_ids)] }}

    @api.constrains('work_date','requested_date','date_from','date_to')
    def check_work_date(self):
        for record in self:
            if record.leave_type_value == 'C-Off':
                if record.work_date:
                    if datetime.strptime(record.requested_date, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
                        raise ValidationError('Please check future date not allowed')

                if record.requested_date and record.work_date and record.compoff_date:
                    requested_date = datetime.strptime(record.requested_date, DEFAULT_SERVER_DATE_FORMAT).date()
                    work_date = datetime.strptime(record.work_date, DEFAULT_SERVER_DATE_FORMAT).date()
                    compoff_date = datetime.strptime(record.compoff_date, DEFAULT_SERVER_DATE_FORMAT).date()
                    availabile_from = requested_date - timedelta(days=30)
                    availabile_upto = work_date + timedelta(days=30)

                    if availabile_from >= work_date:
                        date_value = parser.parse(str(availabile_from))
                        proper_date = date_value.strftime('%B %d, %Y')
                        raise ValidationError(_("Work Date is not Acceptable.\n It must be after %s ") % (proper_date))

                    if availabile_upto < compoff_date:
                        date_value = parser.parse(str(availabile_upto))
                        proper_date = date_value.strftime('%B %d, %Y')
                        raise ValidationError(_("C-Off Date is not Acceptable.\n It must be before %s ") % (proper_date))

                    if work_date >= compoff_date:
                        date_value = parser.parse(str(work_date))
                        proper_date = date_value.strftime('%B %d, %Y')
                        raise ValidationError(_("C-Off Date is not Acceptable.\n It must be after %s ") % (proper_date))

                    # if requested_date >= compoff_date:
                    #     date_value = parser.parse(str(requested_date))
                    #     proper_date = date_value.strftime('%B %d, %Y')
                    #     raise ValidationError(_("C-Off Date is not Acceptable.\n It must be after %s ") % (proper_date))

                if record.work_date and record.branch_id:
                    calendar = self.env['hr.calendar'].search([('branch_id', '=', record.branch_id.id),\
                                                               ('date_from','<=',record.work_date),('date_to','>=',record.work_date)], limit=1)
                    for calendar_line in calendar.calendar_line:
                        if calendar_line.date == record.work_date:
                            if calendar_line.work_type not in ('week_off','holiday'):
                                raise ValidationError("You can't choose this Work Date. This is not a Weekly-Off or Holiday")

                            attendance = self.env['hr.daily.attendance'].search([('branch_id', '=', record.branch_id.id), ('attendance_date', '=', record.work_date),('state','=','done')], limit=1)
                            for attendance_line in attendance.daily_attendance_line:
                                if attendance_line.employee_id == record.employee_id:
                                    if attendance_line.check_in and attendance_line.check_out and attendance_line.worked_hours and attendance_line.attendance_status == 'present':
                                        record.daily_attendance_line = [(6,0, attendance_line.ids)]
                                    else:
                                        raise ValidationError("There is No Attendance record for you on this Work Date.")

                if record.compoff_date and record.branch_id:
                    calendar = self.env['hr.calendar'].search([('branch_id', '=', record.branch_id.id),\
                                                               ('date_from','<=',record.compoff_date),('date_to','>=',record.compoff_date)], limit=1)
                    for calendar_line in calendar.calendar_line:
                        if calendar_line.date == record.compoff_date:
                            if calendar_line.work_type in ('week_off','holiday'):
                                raise ValidationError("You can't choose this C-Off Date. This Date is a Weekly-Off or Holiday")

            if record.leave_type_value == 'MTL':
                if record.date_from and record.date_to:
                    if record.date_from > record.date_to:
                        raise ValidationError('"End" date cannot be earlier than "Start" date.')

#                 domain = [('employee_id', '=', record.employee_id.id),
#                     ('id', '!=', record.id),('type', '=', 'remove'),('year_of_passing', '=', record.year_of_passing),
#                     ('holiday_status_id', '=', record.leave_type_id.id),('state', 'not in', ['cancel', 'refuse'])]
#                 mtl_holidays_sr = record.env['hr.holidays'].search_count(domain)
#                 if mtl_holidays_sr > 1:
#                     raise ValidationError(_('This leave type(%s) was allowed only for Two times. \n You have already availed Two times') % str(record.leave_type_id.name))

    @api.constrains('leave_type_id')
    def check_leave_type(self):
        for record in self:
            if record.leave_type_id and record.leave_type_value and record.leave_type_value == 'MTL':
                if record.employee_id.gender_id.name != 'Female' or record.employee_id.marital == 'single':
                    raise ValidationError('Only Female / Married employees are eligible for this Leave type')

    @api.multi
    def generate_dates(self, date_from, date_to):
        dates = []
        td = timedelta(days=1)
        current_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        while current_date <= datetime.strptime(date_to, "%Y-%m-%d").date():
            dates.append(current_date)
            current_date += td
        return dates

    @api.multi
    def button_request(self):
        for record in self:
            record.write({'state': 'requested'})

    @api.multi
    def button_cancel(self):
        for record in self:
            record.write({'state': 'cancelled'})

    @api.multi
    def button_reject(self):
        for record in self:
            record.write({'state': 'rejected'})

    @api.multi
    def button_approve(self):
        for record in self:
            if record.leave_type_value == 'C-Off':

                allocate = record.env['hr.holidays'].sudo().create({
                    'holiday_type':'employee',
                    'employee_id':record.employee_id.id,
                    'office_type_id':record.employee_id.branch_id.office_type_id.id,
                    'holiday_status_id':record.leave_type_id.id,
                    'name':record.leave_type_id.name,
                    'year_of_passing':record.year_of_passing,
                    'type':'add',
                    'number_of_days_temp':1,
                    'state':'draft',
                })
                allocate.state = 'validate'

                calendar_sr = self.env['hr.calendar'].search([('branch_id', '=', record.employee_id.branch_id.id),('state', '=', 'approve')])
                calendar_line_sr = self.env['hr.calendar.line'].search([('calendar_id', 'in', calendar_sr.ids), ('date', '=', record.compoff_date)])

                leave_list = []
                if calendar_line_sr.work_type == 'work':
                    leave_list.append((0, 0, {
                        'holidays_id': record.id,
                        'calendar_line_id': calendar_line_sr.id,
                        'date': calendar_line_sr.date,
                        'work_type': calendar_line_sr.work_type,
                        'include_all': False,
                        'parts_of_the_day': record.leave_type_id.parts_of_the_day,
                        'status_parts_of_the_day': record.leave_type_id.parts_of_the_day,
                        'leave': True,
                        'status_id': record.leave_type_id.id,
                    }))

                request = record.env['hr.holidays'].sudo().create({
                    'holiday_type':'employee',
                    'employee_id':record.employee_id.id,
                    'office_type_id':record.employee_id.branch_id.office_type_id.id,
                    'holiday_status_id':record.leave_type_id.id,
                    'name':record.leave_type_id.name,
                    'year_of_passing':record.year_of_passing,
                    'date_from':record.compoff_date,
                    'date_to':record.compoff_date,
                    'type': 'remove',
                    'number_of_days_temp': 1,
                    'holiday_calendar_line':leave_list,
                    'state': 'draft',
                })
                request.state = 'validate'

            if record.leave_type_value == 'MTL':

                start_date = datetime.strptime(record.date_from, "%Y-%m-%d")
                end_date = datetime.strptime(record.date_to, "%Y-%m-%d")
                days_count = abs((end_date - start_date).days +1)

                allocate = record.env['hr.holidays'].sudo().create({
                    'holiday_type': 'employee',
                    'employee_id': record.employee_id.id,
                    'office_type_id': record.employee_id.branch_id.office_type_id.id,
                    'holiday_status_id': record.leave_type_id.id,
                    'name': record.leave_type_id.name,
                    'year_of_passing': record.year_of_passing,
                    'type': 'add',
                    'number_of_days_temp': days_count,
                    'state': 'draft',
                })
                allocate.state = 'validate'

                dates = record.generate_dates(record.date_from, record.date_to)
                leave_list = []
                for leave_date in dates:
                    calendar_sr = self.env['hr.calendar'].search([('branch_id', '=', record.employee_id.branch_id.id), ('state', '=', 'approve')])
                    calendar_line_sr = self.env['hr.calendar.line'].search([('calendar_id', 'in', calendar_sr.ids), ('date', '=', leave_date)])

                    if not calendar_line_sr:
                        raise ValidationError(_(' Please Create/Approve the Calendar for the selected Leave duration'))

                    if calendar_line_sr.work_type == 'work':
                        leave_list.append((0, 0, {
                            'holidays_id': record.id,
                            'calendar_line_id': calendar_line_sr.id,
                            'date': calendar_line_sr.date,
                            'work_type': calendar_line_sr.work_type,
                            'include_all': False,
                            'parts_of_the_day': record.leave_type_id.parts_of_the_day,
                            'status_parts_of_the_day': record.leave_type_id.parts_of_the_day,
                            'leave': True,
                            'status_id': record.leave_type_id.id,
                        }))

                request = record.env['hr.holidays'].sudo().create({
                    'holiday_type': 'employee',
                    'employee_id': record.employee_id.id,
                    'office_type_id': record.employee_id.branch_id.office_type_id.id,
                    'holiday_status_id': record.leave_type_id.id,
                    'name': record.leave_type_id.name,
                    'year_of_passing': record.year_of_passing,
                    'date_from': record.date_from,
                    'date_to': record.date_to,
                    'type': 'remove',
                    'number_of_days_temp': days_count,
                    'holiday_calendar_line': leave_list,
                    'state': 'draft',
                })
                request.state = 'validate'

            record.write({'state': 'approved'})
