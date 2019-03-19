from odoo import fields, models, api


class Area(models.Model):
    _name = 'area.area'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    area_type = fields.One2many('area.line', 'area_id')


class AreaLine(models.Model):
    _name = 'area.line'
    _rec_name = 'name'

    name = fields.Char(string="Area")
    description = fields.Text(string="Description")
    area_id = fields.Many2one("area.area")
