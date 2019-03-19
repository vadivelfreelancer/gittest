# -*- coding: utf-8 -*-

from odoo import models, fields,api,_
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class rfid_tracking_data(models.Model):
    _name = 'pappaya.rfid.tracking.data'
    _rec_name = 'student_id'

        
    student_id = fields.Many2one('res.partner', 'Student', domain=[('user_type','=','student')])
    rfid_card_id=fields.Char('RFID Card No.',size=256)

    school_id = fields.Many2one(
    'res.company', 'Branch',select=True)
    
    # university_id = fields.Many2one(
    # 'pappaya.university','Institution')
    #
    # department_id=fields.Many2one(
    # 'pappaya.department','Department')
    
    # grade_id = fields.Many2one(
    #     'pappaya.grade', 'Course',
    #     readonly=True)
    #
    # section_id = fields.Many2one(
    #     'pappaya.batch', 'Batch',
    #     readonly=True)
    
    capture_datetime = fields.Datetime(
        'Date', 
        #~ related='attendance_id.attendance_date', store=True,
        readonly=True)
    
    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')
    
