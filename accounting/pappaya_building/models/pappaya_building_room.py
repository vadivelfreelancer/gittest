from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError

class PappayaBuildingRoom(models.Model):
    _name = 'pappaya.building.room'
    _description = 'Pappaya Building Room'

    name = fields.Char('Room Name', size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string='Building',domain=[('area_type','=','building_area')])
    block_id = fields.Many2one('pappaya.block', string='Block')
    floor_id = fields.Many2one('pappaya.floor', string='Floor')
    room_total_area = fields.Float(string='Room Total Area(Sft)')
    building_purpose =  fields.Many2many('building.purpose',string='Room Purpose')#Clarify
    no_of_classes = fields.Integer('No of Classes',default=1)
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def check_room(self):
        if self.name:
            if len(self.search([('name', '=', (self.name).strip()), ('branch_id', '=', self.branch_id.id),
                                ('building_id', '=', self.building_id.id), ('block_id', '=', self.block_id.id),
                                ('floor_id', '=', self.floor_id.id)])) > 1:
                raise ValidationError("Room already exists.")

    @api.constrains('no_of_classes')
    def validation_number(self):
        if self.no_of_classes < 0:
            raise ValidationError(_("Enter valid No Of Classes"))

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

    @api.onchange('floor_id')
    def onchange_floor_id(self):
        if self.floor_id:
            total_floors = 0.0
            floor_ids = self.env['pappaya.floor'].search([('name','=',self.floor_id.name),('block_id','=',self.block_id.id),('building_id','=',self.building_id.id)])
            for floor in floor_ids:
                total_floors += floor.no_of_rooms
            if total_floors == 1:
                floor_ids = self.env['pappaya.building.room'].search([('floor_id','=',self.floor_id.id)])
                if floor_ids:
                    raise ValidationError(_("Rooms are already assigned. Cannot create another one"))
            else:
                floor_ids = self.env['pappaya.building.room'].search([('floor_id','=',self.floor_id.id)])
                if len(floor_ids) >= total_floors:
                    raise ValidationError(_("Rooms are already assigned. Cannot create another one"))

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
        return super(PappayaBuildingRoom, self).create(vals)

    @api.multi
    def toggle_active(self):
        for record in self:
            if record.active:
                classes = self.env['pappaya.building.class'].search([('room_id','=',self.id),('active','=',True)])
                if classes:
                    classes.write({'active':False})
                record.active = False
            else:
                classes = self.env['pappaya.building.class'].search([('room_id','=',self.id),('active','=',False)])
                if classes:
                    classes.write({'active':True})   
                record.active = True