# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.models import BaseModel

class BaseModelExtend(models.AbstractModel):
    _name = 'basemodel.extend'
    models.BaseModel._navigation = 'id'
    
    def _register_hook(self):
        def _mapped_func(self, func):
            """ Apply function ``func`` on all records in ``self``, and return the
                result as a list or a recordset (if ``func`` returns recordsets).
            """
            if self:
                vals = [func(rec) for rec in self]
                if isinstance(vals[0], BaseModel):
                    try:
                        return vals[0].union(*vals)         # union of all recordsets
                    except:
                        return vals if isinstance(vals, BaseModel) else []
                return vals
            else:
                vals = func(self)
                return vals if isinstance(vals, BaseModel) else []
        
        models.BaseModel._mapped_func = _mapped_func 
        return super(BaseModelExtend, self)._register_hook()