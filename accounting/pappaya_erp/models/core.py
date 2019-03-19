# -*- coding: utf-8 -*-
from openerp import models, fields, api,_
from openerp.exceptions import except_orm, ValidationError

class PappayaCore(models.Model):
    _name = 'pappaya.core'
    _rec_name = 'model_id'
    
    @api.constrains('model_id')
    def check_model_id(self):
        if self.model_id:
            if len(self.search([('model_id', '=', self.model_id.id)])) > 1:
                raise ValidationError("Given model is already exists.")
    
    model_id = fields.Many2one('ir.model',required=1)
    field_ids = fields.Many2many('ir.model.fields', string="Fields", required=1) # domain=[('model_id','=',model_id)],
    
    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            self.field_ids = None
            fields_ids = self.env['ir.model.fields'].search([('model_id','=',self.model_id.id),('copy','=','t'),('ttype','=','char')], order='id asc')
            print('fields_ids.ids :',fields_ids.ids)
            return {'domain': {'field_ids': [('id','in',fields_ids.ids)]}}

class FieldsLog(models.Model):
    _name = "fields.log"

    pappaya_model_log_id = fields.Many2one('pappaya.model.log', string='School Board', ondelete="cascade")
    
    name = fields.Char('Sequence')
    field_label = fields.Char('Field Label')
    field = fields.Char('Field')
    ttype = fields.Char('Type')
    data = fields.Char('Data')
    
class PappayaModelLog(models.Model):
    _name = 'pappaya.model.log'
    _rec_name = 'model_id'
    
    model_id = fields.Many2one('ir.model',required=1)
    field_data_ids = fields.One2many('fields.log', 'pappaya_model_log_id', string="Fields Data") 
#     empty = fields.Boolean(compute='_get_data')
#     
#     @api.multi
#     def _get_data(self):
#         print('1111111111111')
#         self._onchange_model_id()
    
    @api.multi
    def update_data(self):
        self._onchange_model_id()
    
    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            self.field_data_ids = None; field_data_ids = []; count = 0;
            for pc_obj in self.env['pappaya.core'].search([('model_id','=',self.model_id.id)]):
                for imf_obj in pc_obj.field_ids:
                    count += 1;
                    req_field_value = ''
                    model = self.model_id.model
                    model1 = model.replace(".", "_")
                    test11 = "SELECT "+imf_obj.name + " FROM " + model1
                    cr = self._cr
                    cr.execute(test11)
                    for row in cr.dictfetchall():
                        if req_field_value:
                            req_field_value += ','+ row.get(imf_obj.name)
                        else:
                            req_field_value += row.get(imf_obj.name)
                        
                    
                    field_data_ids.append((0,0,{'name': count,
                                                'field_label': imf_obj.field_description,
                                                'ttype': imf_obj.ttype,
                                                'field': imf_obj.name,
                                                'data': req_field_value}))
            self.field_data_ids = field_data_ids
                    
                    
                    
                    
                    
                    