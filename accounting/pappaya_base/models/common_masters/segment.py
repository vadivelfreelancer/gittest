# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PappayaSegment(models.Model):
    _name = 'pappaya.segment'

    name = fields.Char('Segment Name', size=40)
    description = fields.Text(string='Description', size=100)
    segment_squence = fields.Char(string='Series')
    programme_id = fields.Many2one('pappaya.programme', string='Programme')

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Record already exists")

    @api.model
    def create(self, vals):
        res = super(PappayaSegment, self).create(vals)
        sequence_config = self.env['meta.data.master'].search([('name', '=', 'segment')])
        if sequence_config:
            res['segment_squence'] = self.env['ir.sequence'].next_by_code('pappaya.segment') or _('New')
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            segment_mapped = self.env['pappaya.course'].search([('segment_id', '=', rec.id)])
            if segment_mapped:
                raise ValidationError('Sorry,You are not authorized to delete record')
        return super(PappayaSegment, self).unlink()
