from odoo import fields,models,api


class SpecialBatch(models.Model):
    _name = 'special.batch'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    special_batch_line = fields.One2many('special.batch.line', 'special_batch_id')


class SpecialBatchLine(models.Model):
    _name = 'special.batch.line'
    _rec_name = 'name'

    name = fields.Char(string="Subject")
    description = fields.Text(string="Description")
    special_batch_id = fields.Many2one('special.batch')

    @api.multi
    def action_create_special_batch(self):
        return {
            'name': 'Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'special.batch.view',
            'target': 'inline',
        }