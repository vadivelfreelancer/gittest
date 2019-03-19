# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from datetime import datetime, date

class pappaya_enq_wflw_histroy(models.Model):
    """ Workflow history  """
    _name = "pappaya.enq.workflow.history"
    _order = "id asc"
    _description = "workflow history, ..."

    user_id = fields.Many2one('res.users', 'User')
    document_number = fields.Char('Form No')
    movement_stage = fields.Char('Stage Movement')
    updated_on = fields.Datetime('Date')
    enquiry_id = fields.Many2one('pappaya.admission')
    description = fields.Text('Remarks',size=200)
    branch_id = fields.Many2one('operating.unit', string='For Reservation Branch')
    branch_id_at = fields.Many2one('operating.unit', string='At Reservation Branch')
    course_id = fields.Many2one('pappaya.course', string='Course')
    group_id = fields.Many2one('pappaya.group', string='Group')
    batch_id = fields.Many2one('pappaya.batch', string='Batch')
    package_id = fields.Many2one('pappaya.package', string='Package')
    course_package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    amount = fields.Float(string='Amount')
    medium_id = fields.Many2one('pappaya.master', string='Medium')

class pappaya_enq_grade_doc(models.Model):
    """ enq document attachment  """
    _name = "pappaya.enq.grade_doc"
    _order = "id asc"
    _description = "Enquiry grade document attachment ..."

    user_id = fields.Many2one('res.users', 'User Name')
    document_name = fields.Char('Document Name')
    stage_name = fields.Char('Stage Name ')
    enquiry_id = fields.Many2one('pappaya.admission')
    description = fields.Text('Description',size=300)
    document_file = fields.Binary('Attach Document')
    filename = fields.Char('Filename')
    wrk_grade_id=fields.Many2one('pappaya.workflow.grade_doc_config')
    sponsor_id_doc_id=fields.Many2one('pappaya.workflow.sponsorconfig')
    sponsor_id = fields.Many2one('pappaya.sponsor', string='Sponsor Name')
    required=fields.Boolean('Required')
