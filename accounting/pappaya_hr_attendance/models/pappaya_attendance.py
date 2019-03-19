from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta as td
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil import parser
from dateutil.relativedelta import relativedelta
import math



class PappayaAttendance(models.Model):
    _inherit = 'hr.attendance'

    emp_id = fields.Char(related='employee_id.emp_id', string='Employee ID')
    company_id = fields.Many2one('res.company',string='Organization',related='employee_id.company_id')
    branch_id = fields.Many2one('operating.unit', string='Branch',related='employee_id.branch_id',domain=[('type','=','branch')])
    biometric_id = fields.Char(related='employee_id.unique_id', string='Biometric ID')
    attendance_date = fields.Date('Attendance Date')
    attendance_status = fields.Selection([('present', 'Present'), ('absent', 'Absent')], string='Attendance Status')
    check_in = fields.Datetime(string="Check In", required=False)
    designation_id = fields.Many2one('hr.job',related='employee_id.job_id', string='Designation')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),
                              ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')
    
    @api.multi
    @api.constrains('attendance_date')
    def check_date(self):
        for record in self:
            if record.attendance_date and datetime.strptime(record.attendance_date, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
                raise ValidationError('Please check future date not allowed')
            if record.attendance_date and record.employee_id.date_of_joining and record.attendance_date < record.employee_id.date_of_joining:
                doj = parser.parse(record.employee_id.date_of_joining)
                proper_doj = doj.strftime('%d-%m-%Y')
                raise ValidationError(_("Attendance Date is not Acceptable.\n It must be greater than Employee's Date of Joining %s ")%(proper_doj))
