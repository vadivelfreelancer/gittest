# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PappayaUniform(models.Model):
    _name = 'pappaya.uniform'

    @api.constrains('gender', 'school_id')
    def check_gender_branchwise(self):
        if len(self.search([('gender', '=', self.gender),
                            ('school_id', '=', self.school_id.id),
                            ('course_id', '=', self.course_id.id),
                            ('academic_year_id', '=', self.academic_year_id.id)])) > 1:
            raise ValidationError('Uniform already exist..!')

    name = fields.Char(string='Student Name', size=40)
    description = fields.Text(string='Description', size=100)
    is_active = fields.Boolean(string='Active', default=True)
    school_id = fields.Many2one('operating.unit', 'Branch')
    is_co_education = fields.Boolean(string='Is Co-Education')
    course_id = fields.Many2one('pappaya.course', string='Course')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    gender = fields.Selection([('male','Male'),('female', 'Female')], string='Gender')
    total_amount = fields.Float('Total Amount', compute='compute_total_amount')
    uniform_branch_ids = fields.One2many('pappaya.branchwise.uniform', 'uniform_id', string='Uniform Set(s)')

    @api.depends('uniform_branch_ids.amount')
    def compute_total_amount(self):
        amount = 0
        for rec in self.uniform_branch_ids:
            amount += rec.amount
        self.total_amount = amount

    @api.onchange('school_id', 'academic_year_id')
    def onchange_school_id(self):
        self.gender = self.is_co_education = None
        if self.school_id.gender == 'boys':
            self.gender = 'male'
        if self.school_id.gender == 'girls':
            self.gender = 'female'
        if self.school_id.gender == 'co_education':
            self.gender = False
            self.is_co_education = True

        if self.school_id and self.academic_year_id:
            course_domain = []
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        course_domain.append(course_package.course_id.id)
            return {'domain': {'course_id': [('id', 'in', course_domain)]}}

    @api.multi
    @api.depends('gender', 'school_id')
    def name_get(self):
        result = []
        for record in self:
            if record.gender and record.course_id:
                name = str(record.course_id.name) + ' / ' + str(record.gender).title()
            result.append((record.id, name))
        return result


class PappayaBranchwiseUniform(models.Model):
    _name = 'pappaya.branchwise.uniform'
    _description = 'Branchwise Uniform'

    @api.constrains('amount')
    def check_amount(self):
        if self.amount <= 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.constrains('uniform_id', 'uniform_set_id')
    def check_uniform_set(self):
        if len(self.search([('uniform_id', '=', self.uniform_id.id),
                            ('uniform_set_id', '=', self.uniform_set_id.id)])) > 1:
            raise ValidationError('Uniform Set already exist..!')

    uniform_set_id = fields.Many2one('uniform.set', string='Name')
    uniform_id = fields.Many2one('pappaya.uniform', string='Uniform')
    amount = fields.Float(related='uniform_set_id.total_amount', string='Price')

    @api.onchange('amount')
    def onchnage_amount(self):
        if self.amount < 0:
            raise ValidationError('Please enter the valid Price..!')

