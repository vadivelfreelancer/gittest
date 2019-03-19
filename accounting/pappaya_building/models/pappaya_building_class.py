from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError

class PappayaBuildingClass(models.Model):
    _name = 'pappaya.building.class'
    _description = 'Pappaya Building Class'

    name = fields.Char('Class Name', size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string='Building',domain=[('area_type','=','building_area')])
    block_id = fields.Many2one('pappaya.block', string='Block')
    floor_id = fields.Many2one('pappaya.floor', string='Floor')
    room_id = fields.Many2one('pappaya.building.room',string='Room')
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def check_class(self):
        if self.name:
            if len(self.search([('name', '=', (self.name).strip()), ('branch_id', '=', self.branch_id.id),
                                ('building_id', '=', self.building_id.id), ('block_id', '=', self.block_id.id),
                                ('floor_id', '=', self.floor_id.id),('room_id', '=', self.room_id.id)])) > 1:
                raise ValidationError("Class already exists.")

    @api.onchange('branch_id')
    def onchange_branch(self):
        self.building_id = None
        self.floor_id = None
        self.block_id = None

    @api.onchange('building_id')
    def onchange_building(self):
        self.floor_id = None
        self.block_id = None

    @api.onchange('block_id')
    def onchange_floor(self):
        self.floor_id = None
        
    @api.onchange('room_id')
    def onchange_room_id(self):
        if self.room_id:
            total_rooms = 0.0
            room_ids = self.env['pappaya.building.room'].search([('name','=',self.room_id.name),('block_id','=',self.block_id.id),('floor_id','=',self.floor_id.id),('building_id','=',self.building_id.id)])
            for room in room_ids:
                total_rooms += room.no_of_classes
            if total_rooms == 1:
                room_ids = self.env['pappaya.building.class'].search([('room_id','=',self.room_id.id)])
                if room_ids:
                    raise ValidationError(_("Classes are already assigned. Cannot create another one"))
            else:
                room_ids = self.env['pappaya.building.room'].search([('floor_id','=',self.floor_id.id)])
                if len(room_ids) >= total_rooms:
                    raise ValidationError(_("Classes are already assigned. Cannot create another one"))

    @api.model
    def create(self, vals):
        if 'floor_id' in vals:
            floor =  self.env['pappaya.floor'].search([('id', '=', vals['floor_id'])])
            no_of_rooms = floor.no_of_rooms
            existing_rooms = self.search_count([('floor_id','=',floor.id)])
            if no_of_rooms <= existing_rooms:
                raise ValidationError("Cannot Create Room.\n Limit Exceeds")
        if 'room_total_area' in vals:
                floor_total_area = floor.floor_total_area
                used_room_total_area=0.0
                for existing_room in existing_rooms:
                    used_room_total_area += existing_room.room_total_area
                if floor_total_area+vals['room_total_area'] > floor_total_area :
                    raise ValidationError("Area Limit Exceeds.")
        return super(PappayaBuildingClass, self).create(vals)
