from odoo import fields, models, api
# Main Group
class PappayaMainGroup(models.Model):
    _name = 'pappaya.account.main.group'
    
    name = fields.Char('Name',size=100)
    color = fields.Char('Color',size=20)
    description = fields.Text('Description',size=300)
    
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for mg in self:
            if mg.name and mg.color:
                name = str(mg.name) + ':' + str(mg.color)
            else:
                name = str(mg.name)
            result.append((mg.id, name))
        return result
    
# Group
class PappayaAccountGroup(models.Model):
    _name = 'pappaya.account.group'

    name = fields.Char('Name',size=100)
    color = fields.Char('Color',size=20)
    description = fields.Text('Description',size=300)
    main_group_id = fields.Many2one('pappaya.account.main.group', string='Main Group')
    
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for mg in self:
            if mg.name and mg.color:
                name = str(mg.name) + ':' + str(mg.color)
            else:
                name = str(mg.name)
            result.append((mg.id, name))
        return result
    
# Sub Group
class PappayaSubGroup(models.Model):
    _name = 'pappaya.account.sub.group'

    name = fields.Char('Name',size=100)
    color = fields.Char('Color',size=20)
    description = fields.Text('Description',size=300)
    group_id = fields.Many2one('pappaya.account.group', string='Group')
    
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for mg in self:
            if mg.name and mg.color:
                name = str(mg.name) + ':' + str(mg.color)
            else:
                name = str(mg.name)
            result.append((mg.id, name))
        return result
    
# Ledger   
class AccountGroup(models.Model):
    _name = 'pappaya.account.ledger'

    name = fields.Char('Name',size=100)
    color = fields.Char('Color',size=20)
    description = fields.Text('Description',size=300)
    sub_group_id = fields.Many2one('pappaya.account.sub.group', string='Sub Group')
    
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for mg in self:
            if mg.name and mg.color:
                name = str(mg.name) + ':' + str(mg.color)
            else:
                name = str(mg.name)
            result.append((mg.id, name))
        return result
    
#Sub Ledger 
class PappayaAccountAccount(models.Model):
    _name = 'pappaya.account.sub.ledger'
    
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for mg in self:
            if mg.name and mg.color:
                name = str(mg.name) + ':' + str(mg.color)
            else:
                name = str(mg.name)
            result.append((mg.id, name))
        return result
    
    name = fields.Char('Name', required=1 ,size=100)
    color = fields.Char('Color', required=1,size=20)
    description = fields.Text('Description',size=300)
    main_group_id = fields.Many2one('pappaya.account.main.group', string='Main Group', required=1)
    group_id = fields.Many2one('pappaya.account.group', string='Group', required=1)
    sub_group_id = fields.Many2one('pappaya.account.sub.group', string='Sub Group', required=1)
    ledger_id = fields.Many2one('pappaya.account.ledger', string="Ledger", required=1)
    