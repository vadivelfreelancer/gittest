# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
import re
import calendar

# class HrJob(models.Model):
#     _inherit = 'hr.job'
#     _description = 'Designation'
#     
#     wage = fields.Float(string='Wage', required=True,track_visibility="onchange", help="Employee's monthly gross wage.")
#     name = fields.Char(string='Designation', required=True, index=True, translate=True)
#     salary_struct = fields.Many2one('hr.payroll.structure',string='Salary Structure')