# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import math

class NumberOfStudents(models.Model):
    _name = "pappaya.number.students"
    _rec_name = "branch_id"

    name = fields.Char(string='Subjct',size=50)
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    fiscal_year_id = fields.Many2one('fiscal.year', 'Fiscal Year', default=lambda self: self.env['fiscal.year'].search([('active', '=', True)]))
    state_id = fields.Many2one('res.country.state','State', compute='_get_state_program_segment', store=True)
    program_id = fields.Many2one('pappaya.programme','Programme')
    segment_id = fields.Many2one('pappaya.segment','Segment')
    student_line_ids = fields.One2many('pappaya.number.students.line', 'number_id', 'Number of Students')
    active = fields.Boolean(string='Is Active', default=True)
    class_details_get = fields.Boolean('Get Details')

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

    # def get_class_details(self):
    #     if self.student_line_ids.ids == []:
    #         branch_val = self.env['operating.unit'].search([('id','=',self.branch_id.id)])
    #         for course in branch_val.segment_cource_mapping_ids:
    #             if course.fiscal_year_id == self.fiscal_year_id and course.segment_id == self.segment_id and course.programme_id == self.program_id:
    #                 for value in course.course_package_ids:
    #                     student_line = self.env['pappaya.number.students.line']
    #                     student_line.create({
    #                         'number_id' : self.id,
    #                         'class_id' : value.course_id.id,
    #                     })
    #     return

    @api.multi
    @api.onchange('class_details_get')
    def class_details_get_values(self):
        if self.student_line_ids.ids == []:
            branch_val = self.env['operating.unit'].search([('id','=',self.branch_id.id)])
            course_lines = []
            for course in branch_val.segment_cource_mapping_ids:
                if course.fiscal_year_id == self.fiscal_year_id and course.segment_id == self.segment_id and course.programme_id == self.program_id:
                    for value in course.course_package_id:
                        course_lines.append((0, 0, {
                            'number_id' : self.id,
                            'class_id' : value.course_id.id,
                        }))
            self.student_line_ids = course_lines

    @api.model
    def create(self, vals):
        subject_val = self.env['pappaya.number.students'].search([('branch_id', '=', vals['branch_id']),
                                                                       ('program_id', '=', vals['program_id']),
                                                                       ('segment_id', '=', vals['segment_id']),
                                                                       ('fiscal_year_id', '=',vals['fiscal_year_id']),
                                                                       ('active', '=', True)
                                                                       ])
        if subject_val.ids != []:
            raise ValidationError('Record already exists for this Fiscal Year')
        else:
            res = super(NumberOfStudents, self).create(vals)
            return res

    @api.constrains('branch_id','program_id','segment_id','active')
    def check_branch_program_segment_id(self):
        if len(self.search([('branch_id', '=',self.branch_id.id),('program_id', '=', self.program_id.id),('segment_id', '=', self.segment_id.id),\
                            ('fiscal_year_id', '=',self.fiscal_year_id.id),('active', '=', True)])) > 1:
            raise ValidationError("Record already exists for this Fiscal Year")


class NumberOfStudentsLine(models.Model):
    _name = "pappaya.number.students.line"

    @api.depends('old_student_count','dropout_percent','target_count')
    def _get_total_count(self):
        for l in self:
            l.total_count = l.old_student_count - ((l.dropout_percent/100)*l.old_student_count) + l.target_count

    @api.depends('max_intake_count','total_count')
    def _get_number_of_sections(self):
        for l in self:
            if l.max_intake_count >0:
                l.number_sections = math.ceil(l.total_count/l.max_intake_count)

    @api.constrains('old_student_count', 'dropout_percent', 'target_count', 'max_intake_count')
    def check_old_student_count(self):
        for record in self:
            if record.old_student_count < 0:
                raise ValidationError('Old Student Count is not Negative')
            if record.dropout_percent < 0:
                raise ValidationError('Dropout Percentage is not Negative')
            if record.target_count < 0:
                raise ValidationError('Target Count is not Negative')
            if record.max_intake_count < 0:
                raise ValidationError('Max. Intake Count is not Negative')

    number_id = fields.Many2one('pappaya.number.students', string='Number ID')
    class_id = fields.Many2one('pappaya.course', string='Course Name')
    old_student_count = fields.Integer('Existing Student Count')
    dropout_percent = fields.Integer('Dropout %')
    target_count = fields.Integer('Additional Projected Count')
    total_count = fields.Integer('No. of Students', compute='_get_total_count', store=True)
    max_intake_count = fields.Integer('Max. Intake Students Count/Section')
    number_sections = fields.Integer('No. of Sections', compute='_get_number_of_sections', store=True)
