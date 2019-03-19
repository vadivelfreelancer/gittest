from odoo import fields, models, api


class PappayaTracks(models.Model):
    _name = 'pappaya.tracks'

    name = fields.Char()
    description = fields.Text()
