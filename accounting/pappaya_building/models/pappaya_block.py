from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class PappayaBlock(models.Model):
    _name = 'pappaya.block'
    _description = 'Pappaya Block'

    name = fields.Char('Block Name', size=40)
    area = fields.Char('Block Area', size=64)
    no_of_floors = fields.Integer(string='No Of Floors')
    number = fields.Char('Block Number',size=10)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string='Building',domain=[('area_type','=','building_area')])
    floor_id = fields.Many2one('pappaya.floor', string='Floor')
    block_total_area = fields.Float(string='Block Total Area(Sft)')
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def check_block_name(self):
        if self.name:
            if len(self.search([('name', '=', (self.name).strip()),('branch_id', '=', self.branch_id.id),
                                ('building_id', '=', self.building_id.id)])) > 1:
                raise ValidationError("Block already exists.")

    @api.onchange('branch_id')
    def onchange_branch(self):
        self.building_id = None
        
    @api.constrains('block_total_area','no_of_floors')
    def validation_number(self):
        if self.block_total_area < 0:
            raise ValidationError(_("Enter valid Block Total Area(Sft)"))
        if self.no_of_floors < 0:
            raise ValidationError(_("Enter valid No Of Blocks"))
 
    @api.onchange('block_total_area')
    def onchange_block_total_area(self):
        if self.block_total_area > 0.0:
            total_area = 0.0
            total_blocks = 0.0
            building_ids = self.env['pappaya.building'].search([('name','=',self.building_id.name)])
            for builds in building_ids:
                total_blocks += builds.no_of_blocks
                total_area  += builds.building_total_area
            block_ids = self.env['pappaya.block'].search([('building_id','=',self.building_id.id)])
            blocked_area = 0.0
            for block in block_ids:
                blocked_area += block.block_total_area
            if total_blocks == 1 and self.block_total_area < (total_area - blocked_area):
                self.block_total_area = total_area
                raise ValidationError(_("Total block area should not be lesser than assigned"))
            elif total_blocks == 1 and self.block_total_area > (total_area - blocked_area):
                self.block_total_area = total_area
                raise ValidationError(_("Total block area should not be greater than assigned"))
            elif total_blocks > 1 and self.block_total_area < (total_area - blocked_area):
                if len(block_ids) == total_blocks - 1 and self.block_total_area < (total_area-blocked_area):
                    raise ValidationError(_("Total block area should not be lesser than assigned"))
            elif total_blocks > 1 and self.block_total_area < (total_area - blocked_area):
                if len(block_ids) == total_blocks - 1 and self.block_total_area > (total_area -blocked_area):
                    raise ValidationError(_("Total block area should not be greater than assigned"))
            elif total_blocks == len(block_ids):
                prev_block_id = self.env['pappaya.block'].search([('id','!=',self._origin.id),('building_id','=',self.building_id.id)])
                prev_block_area = 0.0
                for prev in prev_block_id:
                    prev_block_area += prev.block_total_area
                if (self.block_total_area + prev_block_area) > blocked_area:
                    raise ValidationError(_("Total block area should not be greater than assigned"))
                elif (self.block_total_area + prev_block_area) < blocked_area:
                    raise ValidationError(_("Total block area should not be lesser than assigned"))
                

    @api.onchange('building_id')
    def onchange_building_id(self):
        if self.building_id:
            total_area = 0.0
            total_blocks = 0.0
            building_ids = self.env['pappaya.building'].search([('name','=',self.building_id.name)])
            for builds in building_ids:
                total_blocks += builds.no_of_blocks
                total_area  += builds.building_total_area
            if total_blocks == 1:
                block_ids = self.env['pappaya.block'].search([('building_id','=',self.building_id.id)])
                if block_ids:
                    raise ValidationError(_("Blocks are already assigned. Cannot create another one"))
                self.block_total_area = total_area
            else:
                block_ids = self.env['pappaya.block'].search([('building_id','=',self.building_id.id)])
                if len(block_ids) >= total_blocks:
                    raise ValidationError(_("Blocks are already assigned. Cannot create another one"))
                blocked_area = 0.0
                for block in block_ids:
                    blocked_area += block.block_total_area
                self.block_total_area = total_area - blocked_area

    @api.model
    def create(self, vals):
        if 'building_id' in vals:
            building =  self.env['pappaya.building'].search([('id', '=', vals['building_id'])])
            no_of_blocks = building.no_of_blocks
            existing_blocks = self.search([('building_id','=',building.id)])
            if no_of_blocks <= len(existing_blocks):
                raise ValidationError("Cannot Create Block.\n Limit Exceeds")
            if 'block_total_area' in vals:
                building_block_area = building.building_total_area
                used_block_total_area=0.0
                if existing_blocks:
                    for existing_block in existing_blocks:
                        used_block_total_area += existing_block.block_total_area
                    if used_block_total_area+vals['block_total_area'] > building_block_area :
                        raise ValidationError("Area Limit Exceeds.")
        return super(PappayaBlock, self).create(vals)

    @api.multi
    def toggle_active(self):
        for record in self:
            if record.active:
                floors = self.env['pappaya.floor'].search([('block_id','=',self.id),('active','=',True)])
                rooms = self.env['pappaya.building.room'].search([('block_id','=',self.id),('active','=',True)])
                classes = self.env['pappaya.building.class'].search([('block_id','=',self.id),('active','=',True)])
                if floors:
                    floors.write({'active':False})
                if rooms:
                    rooms.write({'active':False})
                if classes:
                    classes.write({'active':False})
                record.active = False
            else:
                floors = self.env['pappaya.floor'].search([('block_id','=',self.id),('active','=',False)])
                rooms = self.env['pappaya.building.room'].search([('block_id','=',self.id),('active','=',False)])
                classes = self.env['pappaya.building.class'].search([('block_id','=',self.id),('active','=',False)])
                if floors:
                    floors.write({'active':True})
                if rooms:
                    rooms.write({'active':True})
                if classes:
                    classes.write({'active':True})   
                record.active = True
