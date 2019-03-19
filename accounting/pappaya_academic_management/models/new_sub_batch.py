from odoo import fields, models, api


class NewSubBatch(models.Model):
    _name = 'new.subbatch'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    sub_batch = fields.Many2one("sub.batch", string="Sub Batch")
    new_subbatch_type = fields.One2many('new.subbatch.line', 'new_subbatch_id')


class NewSubBatchLine(models.Model):
    _name = 'new.subbatch.line'
    _rec_name = 'name'

    name = fields.Char(string="New Sub Batch")
    sub_batch = fields.Many2one("sub.batch", string="Sub Batch")
    description = fields.Text(string="Description")
    new_subbatch_id = fields.Many2one("new.subbatch")
