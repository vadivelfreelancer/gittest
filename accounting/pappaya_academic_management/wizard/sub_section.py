from odoo import fields,models,api


class SubSectionView(models.TransientModel):
    _name = 'sub.section.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    character_type = fields.Many2one('character.type', string="Character")
    sub_section_lines = fields.Many2many('sub.section.line')

    @api.model
    def default_get(self, fields):
        res = super(SubSectionView, self).default_get(fields)
        sub_section = self.env['sub.section.line'].search([])
        res['sub_section_lines'] = sub_section.ids
        return res


