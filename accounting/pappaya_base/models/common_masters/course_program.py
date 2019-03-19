# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

class PappayaCourseProgram(models.Model):
    _name = 'pappaya.course.program'

    name = fields.Char('Course Program Name', size=124)
    course_id = fields.Many2one('pappaya.course','Course')
    group_id = fields.Many2one('pappaya.group',"Group")
    batch_id = fields.Many2one('pappaya.batch','Batch')
    program_id = fields.Many2one('pappaya.programme','Programme')


    @api.one
    @api.constrains('course_id', 'group_id', 'batch_id', 'program_id')
    def check_name_exists(self):
        if self.course_id and self.group_id and self.batch_id and self.program_id:
            if len(self.search([('course_id', '=', self.course_id.id),('group_id', '=', self.group_id.id),
                                ('batch_id', '=', self.batch_id.id),('program_id', '=', self.program_id.id)])) > 1:
                raise ValidationError('CGB-Program is already exists for selected CGBP.')
            
    @api.model
    def create(self, vals):
        res = super(PappayaCourseProgram, self).create(vals)
        for c in res:
            name = ''
            if c.course_id and c.group_id and c.batch_id and c.program_id:
                name = str(c.course_id.name)+'-' + str(c.group_id.name) + '-' + str(c.batch_id.name) + '-' + str(c.program_id.name)
            if name:
                c.name = name
        return res

    @api.onchange('course_id')
    def onchange_course_id(self):
        if self.course_id:
            self.group_id = self.batch_id = self.program_id = None

    @api.onchange('group_id')
    def onchange_group_id(self):
        if self.group_id:
            self.batch_id = self.program_id = None

    @api.onchange('batch_id')
    def onchange_batch_id(self):
        if self.batch_id:
            self.program_id = None

    @api.onchange('course_id','group_id','batch_id','program_id')
    def onchange_course_group_batch_program_id(self):
        for record in self:
            if record.course_id and record.group_id and record.batch_id and record.program_id:
                record.name = str(record.course_id.name) + '-' + str(record.group_id.name) + '-' + str(record.batch_id.name) + '-' + str(record.program_id.name)
            else:
                record.name = False


