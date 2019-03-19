from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class MainBuildingMapping(models.Model):
    _name = 'main.building.mapping'
    _description = 'Main Building Mapping'

    branch_id = fields.Many2one('operating.unit', string="Branch")
    main_building_id = fields.Many2one('pappaya.building', string='Main Building')
    building_id = fields.Many2many('pappaya.building', string='Building')
