from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError

class PappayaFloor(models.Model):
    _name = 'pappaya.floor'
    _description = 'Pappaya Floor'

    name = fields.Char('Floor Name', size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string='Building',domain=[('area_type','=','building_area')])
    block_id = fields.Many2one('pappaya.block', string='Block')
    no_of_rooms = fields.Integer(string='No. Of Rooms')
    floor_total_area = fields.Float(string='Floor Total Area(Sft)')
    building_purpose =  fields.Many2many('building.purpose',string='Floor Purpose')#Clarify
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def check_floor(self):
        if self.name:
            if len(self.search([('name', '=', (self.name).strip()),('branch_id', '=', self.branch_id.id),
                                ('building_id', '=', self.building_id.id),('block_id', '=', self.block_id.id)])) > 1:
                raise ValidationError("Floor already exists.")

    @api.constrains('no_of_ROOMS')
    def validation_number(self):
        if self.no_of_rooms < 0:
            raise ValidationError(_("Enter valid No. Of Rooms"))

    @api.onchange('branch_id')
    def onchange_branch(self):
        self.building_id = None
        self.block_id = None

    @api.onchange('building_id')
    def onchange_building(self):
        self.block_id = None

    @api.onchange('block_id')
    def onchange_block_id(self):
        if self.block_id:
            total_blocks = 0.0
            block_ids = self.env['pappaya.block'].search([('name','=',self.block_id.name),('building_id','=',self.building_id.id)])
            for block in block_ids:
                total_blocks += block.no_of_floors
            if total_blocks == 1:
                floor_ids = self.env['pappaya.floor'].search([('block_id','=',self.block_id.id)])
                if floor_ids:
                    raise ValidationError(_("Floors are already assigned. Cannot create another one"))
            else:
                floor_ids = self.env['pappaya.floor'].search([('block_id','=',self.block_id.id)])
                if len(floor_ids) >= total_blocks:
                    raise ValidationError(_("Floors are already assigned. Cannot create another one"))

    @api.model
    def create(self, vals):
        if 'block_id' in vals:
            block =  self.env['pappaya.block'].search([('id', '=', vals['block_id'])])
            no_of_floors = block.no_of_floors
            existing_floors = self.search_count([('block_id','=',block.id)])
            if no_of_floors <= existing_floors:
                raise ValidationError("Cannot Create Floor.\n Limit Exceeds")
        if 'floor_total_area' in vals:
                block_total_area = block.block_total_area
                used_floor_total_area=0.0
                for existing_floor in existing_floors:
                    used_floor_total_area += existing_floor.floor_total_area
                if used_floor_total_area+vals['floor_total_area'] > block_total_area :
                    raise ValidationError("Area Limit Exceeds.")
        return super(PappayaFloor, self).create(vals)

    @api.multi
    def toggle_active(self):
        for record in self:
            if record.active:
                rooms = self.env['pappaya.building.room'].search([('floor_id','=',self.id),('active','=',True)])
                classes = self.env['pappaya.building.class'].search([('floor_id','=',self.id),('active','=',True)])
                if rooms:
                    rooms.write({'active':False})
                if classes:
                    classes.write({'active':False})
                record.active = False
            else:
                rooms = self.env['pappaya.building.room'].search([('floor_id','=',self.id),('active','=',False)])
                classes = self.env['pappaya.building.class'].search([('floor_id','=',self.id),('active','=',False)])
                if rooms:
                    rooms.write({'active':True})
                if classes:
                    classes.write({'active':True})   
                record.active = True