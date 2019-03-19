from odoo import fields,models,api


class SubBatch(models.Model):
    _name = 'sub.batch'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    subbatch_type = fields.One2many('subbatch.line', 'subbatch_id')


class SubjectOrderLine(models.Model):
    _name = 'subbatch.line'
    _rec_name = 'name'

    name = fields.Char(string="Subject")
    description = fields.Text(string="Description")
    subbatch_id = fields.Many2one('sub.batch')

    @api.multi
    def action_create_subbatch_line(self):
        return {
            'name': 'Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sub.batch.view',
            'target': 'inline',
        }