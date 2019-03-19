from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil import parser
from dateutil.relativedelta import relativedelta
import math
import logging
import threading

_logger = logging.getLogger(__name__)



class PappayaEmployeeAttendance(models.Model):
    _name = 'hr.employee.attendance'
    _rec_name = 'employee_id'


    date_from = fields.Date(string='From date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To date', required=True, default=lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    emp_id = fields.Char('Employee ID', size=6, required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    branch_id = fields.Many2one('operating.unit', string='Branch', domain=[('type', '=', 'branch')], required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    employee_attendance_line = fields.One2many('hr.employee.attendance.line', 'employee_attendance_id', string='Employee Attendance Line')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', readonly=True,track_visibility='onchange', copy=False, default='draft')

    @api.onchange('emp_id','employee_id')
    def onchange_emp_id(self):
        for record in self:
            if record.emp_id:
                employee = self.env['hr.employee'].search([('emp_id', '=', record.emp_id), ('active', '=', True)])
                if employee:
                    record.employee_id = employee.id
                    record.branch_id = employee.branch_id.id
                    record.department_id = employee.department_id.id
                else:
                    record.employee_id = None
            if record.employee_id:
                record.emp_id = record.employee_id.emp_id
                record.branch_id = record.employee_id.branch_id.id
                record.department_id = record.employee_id.department_id.id

    @api.onchange('emp_id', 'employee_id', 'date_from', 'date_to')
    def onchange_employee_id(self):
        for record in self:
            if record.emp_id and record.employee_id and record.date_from and record.date_to:
                attendance_line = self.env['hr.daily.attendance.line'].search([('employee_id','=',record.employee_id.id),('state','in',('draft','done')),\
                                                                               ('attendance_date','>=',record.date_from),('attendance_date','<=',record.date_to)], order='attendance_date')
                employee_attendance_line = []
                for attendance in attendance_line:
                    employee_attendance_line.append((0,0, {
                                             'daily_attendance_line_id' : attendance.id,
                                             'attendance_date' : attendance.attendance_date,
                                             'biometric_id' : attendance.biometric_id,
                                             'check_in' : attendance.check_in,
                                             'check_out': attendance.check_out,
                                             'worked_hours' : attendance.worked_hours,
                                             'attendance_status' : attendance.attendance_status,
                                             'state' : 'draft'
                                     }))
                record.employee_attendance_line = employee_attendance_line

    def attendance_confirm(self):
        for record in self:
            for line in record.employee_attendance_line:
                attendance_line = self.env['hr.daily.attendance.line'].search([('id', '=', line.daily_attendance_line_id.id)])
                attendance_line.write({
                    'attendance_date': line.attendance_date,
                    'biometric_id': line.biometric_id,
                    'check_in': line.check_in,
                    'check_out': line.check_out,
                    'worked_hours': line.worked_hours,
                    'attendance_status': line.attendance_status,
                })
                line.state = 'done'
            record.state = 'done'


class PappayaEmployeeAttendanceLine(models.Model):
    _name = 'hr.employee.attendance.line'


    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = datetime.strptime(attendance.check_out, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(attendance.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                attendance.worked_hours = delta.total_seconds() / 3600.0

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))

    employee_attendance_id = fields.Many2one('hr.employee.attendance',ondelete='cascade')
    daily_attendance_line_id = fields.Many2one('hr.daily.attendance.line', string='Daily Attendance Line')
    attendance_date = fields.Date('Attendance Date')
    employee_id = fields.Many2one('hr.employee', string='Employee ID')
    biometric_id = fields.Char('Biometric ID')
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)
    attendance_status = fields.Selection([('present', 'Present'), ('absent', 'Absent')], string='Attendance Status')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')