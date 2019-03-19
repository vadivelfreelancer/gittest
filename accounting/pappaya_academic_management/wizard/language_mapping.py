from odoo import fields, models, api


class LanguageMappingView(models.Model):
    _name = 'language.mapping.view'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    subject = fields.Many2one('subject.line', string="Subject")
    lang_mapping = fields.Many2many('language.mapping.line')

    @api.model
    def default_get(self, fields):
        res = super(LanguageMappingView, self).default_get(fields)
        lang_mapping = self.env['language.mapping.line'].search([])
        res['lang_mapping'] = lang_mapping.ids
        return res
