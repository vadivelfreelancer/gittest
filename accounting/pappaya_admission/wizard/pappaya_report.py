# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PappayaReport(models.TransientModel):
    _name = "pappaya.report"
    _description = 'Pappaya Report'

    branch_ids = fields.Many2many('res.company', string='Branch')

    @api.multi
    def action_get_pdf(self):
        return

    @api.multi
    def action_get_excel(self):
        return
