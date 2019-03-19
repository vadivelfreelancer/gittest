from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
from datetime import datetime, date, timedelta as td
from dateutil.relativedelta import relativedelta
import re


# 
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    
    
    @api.multi
    def unlink(self):
        raise ValidationError('Sorry,You are not authorized to delete record.\nRather,You can deactivate the employee.')
        return super(HrEmployee, self).unlink()
    
