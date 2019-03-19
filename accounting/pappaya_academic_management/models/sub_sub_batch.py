from odoo import fields,models,api


class SubSubBatch(models.Model):
    _name = 'sub.sub.batch'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    sub_sub_batch_line = fields.One2many('sub.sub.batch.line', 'sub_sub_batch_id')


class SubjectOrderLine(models.Model):
    _name = 'sub.sub.batch.line'
    _rec_name = 'name'

    name = fields.Char(string="Sub Sub Batch")
    description = fields.Text(string="Description")
    sub_sub_batch_id = fields.Many2one('sub.sub.batch')

    @api.multi
    def action_create_sub_sub_batch_line(self):
        return {
            'name': 'Sub Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sub.sub.batch.view',
            'target': 'inline',
        }