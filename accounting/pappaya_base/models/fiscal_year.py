# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class FiscalYear(models.Model):
    _name = "fiscal.year"

    
    name = fields.Char(string='Fiscal Year', required=True, translate=True,size=20)
    date_start = fields.Date(string='Start date', required=True)
    date_end = fields.Date(string='End date', required=True)
    active = fields.Boolean(help="The active field allows you to hide the date range without removing it.", default=True)
    

    @api.constrains('date_start', 'date_end')
    def _validate_range(self):
        for this in self:
            start = fields.Date.from_string(this.date_start)
            end = fields.Date.from_string(this.date_end)
            if start > end:
                raise ValidationError(_("%s is not a valid range (%s > %s)") % (this.name, this.date_start, this.date_end))
            date_start  = datetime.strptime(self.date_start, '%Y-%m-%d').date()
            date_end    = datetime.strptime(self.date_end, '%Y-%m-%d').date()
            if len(self.sudo().search([('date_start','<=',date_start),
                            ('date_end','>=',date_start),'|',('active','=',True),('active','=',False)
                            ])) > 1:
                raise ValidationError("Fiscal Year start date already exists.")
            
            if len(self.sudo().search([('date_start','<=',date_end),
                                ('date_end','>=',date_end),'|',('active','=',True),('active','=',False)
                                ])) > 1:
                raise ValidationError("Fiscal Year date end already exists.")

    @api.constrains('active')
    def check_fiscal_year(self):
        if self.date_start and self.date_end:
            if len(self.search([('active', '=', True)])) > 1:
                raise ValidationError("Fiscal Year already exists. Deactivate the Previous Record.")
            
            
            