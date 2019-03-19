from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class MaterialSetAdd(models.TransientModel):
    _name = 'material.set.add'
    _rec_name = 'product_set_id'

    product_set_id = fields.Many2one('material.set', string='Material Set')
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Material Unit of Measure'), default=1)

    @api.multi
    def add_set(self):
        """ Add product set, multiplied by quantity in sale order line """
        so_id = self._context['active_id']
        if not so_id:
            return
        so = self.env['branchwise.material'].browse(so_id)
        max_sequence = 0
        if so.branchwise_material_line_ids:
            max_sequence = max([line.sequence for line in so.branchwise_material_line_ids])
        sale_order_line = self.env['branchwise.material.line']
        for set_line in self.product_set_id.set_line_ids:
            sale_order_line.create(
                self.prepare_sale_order_line_data(so_id, self.product_set_id, set_line, max_sequence=max_sequence))

    def prepare_sale_order_line_data(self, sale_order_id, set, set_line, max_sequence=0):
        sale_line = self.env['branchwise.material.line'].new({
            'from_material_set': 'yes',
            'material_id':sale_order_id,
            'product_id': set_line.product_id.id,
            'product_uom_qty': set_line.quantity,
            'price_unit': set_line.price,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'sequence': max_sequence + set_line.sequence,
        })
        line_values = sale_line._convert_to_write(sale_line._cache)
        return line_values
