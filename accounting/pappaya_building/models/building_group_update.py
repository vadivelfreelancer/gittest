from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

class BuildingGroupUpdate(models.Model):
    _name = 'building.group.update'
    _rec_name = 'branch_id'

    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string="Building")
    apex_id = fields.Many2one('operating.unit', string="Apex")

