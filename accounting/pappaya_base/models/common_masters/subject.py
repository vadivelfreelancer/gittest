# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PappayaSubject(models.Model):
    _name = 'pappaya.subject'

    name = fields.Char(string='Subject Name', size=40)
    sequence = fields.Integer(string='Sequence')
    description = fields.Text(string='Description', size=100)
    branch_id = fields.Many2one('operating.unit', 'Branch')
    course_id = fields.Many2many('pappaya.course', string='Course')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    institution_type = fields.Selection([('college', 'College'), ('school', 'School')], string="Type")

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        val = []
        if self.branch_id:
            branch_val = self.env['res.company'].search([('id', '=', self.branch_id.id)])
            for course in branch_val.course_config_ids:
                if course.academic_year_id == self.academic_year_id:
                    for value in course.course_package_ids:
                        val.append(value.course_id.id)
                    return {'domain': {'course_id': [('id', 'in', tuple(val))]}}

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Subject already exists")
