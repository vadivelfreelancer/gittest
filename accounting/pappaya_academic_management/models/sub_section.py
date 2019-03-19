from odoo import fields, models, api


class SubSection(models.Model):
    _name = 'sub.section'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    character_type = fields.Many2one('character.type', string="Character")
    sub_section_type = fields.One2many('sub.section.line','sub_section_id')


class ExamType(models.Model):
    _name = 'character.type'
    _rec_name = 'name'

    name = fields.Char(string='Character')


class ExamCourseLine(models.Model):
    _name = 'sub.section.line'
    _rec_name = 'name'

    name = fields.Char(string="Exam Course")
    character_type = fields.Many2one('character.type', string="Character")
    from_number = fields.Char(string="From No.")
    to_number = fields.Char(string="To No.")
    description = fields.Text(string="Description")
    sub_section_id = fields.Many2one("sub.section")
