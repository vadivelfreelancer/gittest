# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError
import re
from datetime import datetime




class PappayaConcessionReason(models.Model):
    _name = 'pappaya.concession.reason'



    name = fields.Char('Name',size=100)
    description = fields.Text('Description' ,size=200)
