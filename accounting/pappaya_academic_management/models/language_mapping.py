from odoo import fields, models, api


class LanguageMapping(models.Model):
    _name = 'language.mapping'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    subject = fields.Many2one('subject.line', string="Subject")
    lang_mapping = fields.One2many('language.mapping.line', 'lang_mapping_id')


class PcSubjectLine(models.Model):
    _name = 'language.mapping.line'

    sub = fields.Many2one('subject.line', string="Subject")
    subject = fields.Many2one('subject.line', string="Mapping Subject")
    description = fields.Text(string="Description")
    lang_mapping_id = fields.Many2one('language.mapping')

    @api.multi
    def action_create_mapping_language_line(self):
        return {
            'name': 'Subject Mapping Wise Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'language.mapping.view',
            'target': 'inline',
        }