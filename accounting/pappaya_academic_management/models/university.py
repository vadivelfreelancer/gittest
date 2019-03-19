from odoo import fields,models,api


class University(models.Model):
    _name = 'university.university'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    university_type = fields.One2many('university.line','university_id')


class UniversityLine(models.Model):
    _name = 'university.line'
    _rec_name = 'name'

    name = fields.Char(string="University")
    description = fields.Text(string="Description")
    university_id = fields.Many2one("university.university")
