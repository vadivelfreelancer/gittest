# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm
from odoo.exceptions import ValidationError
from datetime import datetime


class AttendanceHistoryTable(models.Model):
    _name='attendance.history.table'
    
    fixedstr1 = fields.Char('FIXED STR 1', index=True)
    event_dt = fields.Date('EVENT DT', index=True)
    event_time = fields.Datetime('EVENT TIME', index=True)
    controller_name = fields.Char('CONTROLLER NAME', index=True)
    fixedstr2 = fields.Char('FIXED STR 2', index=True)
    userid = fields.Char('USER ID', index=True)
    username = fields.Char('USER NAME', index=True)
    department = fields.Char('DEPARTMENT', index=True)
    access_mode = fields.Char('ACCESS MODE', index=True)
    doorstate = fields.Char('DOOR STATE', index=True)
    functionkey = fields.Char('FUNCTION KEY', index=True)
    description = fields.Char('DESCRIPTION', index=True)
    userid1 = fields.Integer('USER ID 1', index=True)
    flag = fields.Integer('FLAG', index=True)
    
    
    
    