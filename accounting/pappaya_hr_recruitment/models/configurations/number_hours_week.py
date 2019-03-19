# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date

class NumberHoursSubject(models.Model):
    _name = "pappaya.number.hours.subject"
    _rec_name = "state_id"

    name = fields.Char(string='Subject',size=50)
    fiscal_year_id = fields.Many2one('fiscal.year', 'Fiscal Year', default=lambda self: self.env['fiscal.year'].search([('active', '=', True)]))
    state_id = fields.Many2one('res.country.state', 'State', domain=[('country_id.is_active','=',True)])
    program_id = fields.Many2one('pappaya.programme', 'Programme')
    segment_id = fields.Many2one('pappaya.segment', 'Segment')
    subject_line_ids = fields.One2many('pappaya.number.hours.subject.line', 'number_id', 'Number of Students')
    active = fields.Boolean(string='Is Active', default=True)
    subject_details_get = fields.Boolean('Get Details')

    @api.onchange('state_id')
    def onchange_state_id(self):
        for record in self:
            record.program_id = record.segment_id = None
            segment_ids = program_ids = []
            branch_val = self.env['operating.unit'].search([('state_id', '=', record.state_id.id)])
            for branch in branch_val:
                for lines in branch.segment_cource_mapping_ids:
                    if lines.fiscal_year_id.id == record.fiscal_year_id.id and lines.active:
                        segment_ids.append(lines.segment_id.id)
                        program_ids.append(lines.programme_id.id)
            return {'domain': {'program_id': [('id', 'in', program_ids)],'segment_id': [('id', 'in', segment_ids)]}}

    @api.multi
    @api.onchange('subject_details_get')
    def subject_details_get_values(self):
        if self.subject_line_ids.ids == []:
            course_value = []
            subject_value = []
            subject_lines = []
            branch_val = self.env['operating.unit'].search([('state_id', '=', self.state_id.id)])
            for branch in branch_val:
                for course in branch.segment_cource_mapping_ids:
                    if course.fiscal_year_id == self.fiscal_year_id and course.segment_id == self.segment_id and course.programme_id == self.program_id:
                        for value in course.course_package_id:
                            if value.course_id and value.course_id.id not in course_value:
                                course_value.append(value.course_id.id)
                                subject_val = self.env['pappaya.subject'].search([('course_id', '=', value.course_id.id)])
                                for subject in subject_val:
                                    # if subject and subject.id not in subject_value:
                                    #     subject_value.append(subject.id)
                                    subject_lines.append((0, 0, {
                                        'number_id': self.id,
                                        'class_id': value.course_id.id,
                                        'subject_id': subject.id,
                                    }))
            self.subject_line_ids = subject_lines

    @api.model
    def create(self, vals):
        subject_val = self.env['pappaya.number.hours.subject'].search([('state_id', '=', vals['state_id']),
                                                         ('program_id', '=', vals['program_id']),
                                                         ('segment_id', '=', vals['segment_id']),
                                                         ('fiscal_year_id', '=', vals['fiscal_year_id']),
                                                         ('active', '=', True)
                                                         ])
        if subject_val.ids != []:
            raise ValidationError('Record already exists for this Fiscal Year')
        else:
            res = super(NumberHoursSubject, self).create(vals)
            return res

    @api.constrains('state_id', 'program_id', 'segment_id', 'active')
    def check_branch_program_segment_id(self):
        if len(self.search([('state_id', '=', self.state_id.id),('program_id', '=', self.program_id.id),('segment_id', '=', self.segment_id.id), \
                            ('fiscal_year_id', '=', self.fiscal_year_id.id), ('active', '=', True)])) > 1:
            raise ValidationError("Record already exists for this Fiscal Year")


class numberHoursSubjectLine(models.Model):
    _name = "pappaya.number.hours.subject.line"

    @api.constrains('number_hours')
    def check_old_student_count(self):
        for record in self:
            if record.number_hours < 0:
                raise ValidationError('Weekly Subject Hours/Week is not Negative')

    number_id = fields.Many2one('pappaya.number.hours.subject', string='Number ID')
    class_id = fields.Many2one('pappaya.course', string='Course')
    subject_id = fields.Many2one('pappaya.subject', string='Subject')
    number_hours = fields.Integer('Weekly Subject Hours/Week')
