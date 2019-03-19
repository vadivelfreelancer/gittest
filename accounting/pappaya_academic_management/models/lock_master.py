from odoo import api, fields, models


class LockLock(models.Model):
    _name = 'lock.lock'

    sub_batch = fields.Many2one("subbatch.line", string="Sub Batch")
    sub_section = fields.Many2one("sub.section.line", string="Sub Section")
    hyd_dn = fields.Boolean("HYD-DN", )
    adoni = fields.Boolean("ADONI", )

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])