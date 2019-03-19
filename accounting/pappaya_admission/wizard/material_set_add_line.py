from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class MaterialSetAddLine(models.TransientModel):
    _name = 'material.set.add.line'
    _order = 'sequence'

    wiz_id = fields.Many2one('material.set.add', string="Material Set Add")
    product_set_line_id = fields.Many2one('material.set.line', string="Material Set Line")
    product_set_id = fields.Many2one('material.set', string='Material Set',related='product_set_line_id.product_set_id')
    sequence = fields.Integer(string='Sequence')
    product_template_id = fields.Many2one('product.template', string='Material')
    product_variant_ids = fields.Many2many('product.product',domain="""['&',('sale_ok', '=', True),('product_tmpl_id', '=', product_template_id),]""", string='Variant')
    quantity = fields.Float(string='Quantity',digits=dp.get_precision('Material Unit of Measure'))
    price = fields.Float(string='Material Per Price')
    total_price = fields.Float(string='Total Price')

    @api.onchange('product_template_id')
    def _onhange_product_template_id(self):
        for record in self:
            variants = record.product_template_id.product_variant_ids
            if len(variants) == 1:
                record.product_variant_ids = [(6, 0, variants.ids)]
            else:
                record.product_variant_ids = [(5, 0, 0)]


class MaterialSetAdd(models.TransientModel):
    _inherit = 'material.set.add'

    product_set_id = fields.Many2one('material.set', 'Material Set')
    set_line_ids = fields.One2many('material.set.add.line', 'wiz_id', string='Material Set Add Line')

    @api.onchange('product_set_id')
    def _onchange_product_set_id(self):
        vals = []
        if self.product_set_id:
            for line in self.product_set_id.set_line_ids:
                if not line.product_template_id:
                    raise ValidationError(_("No selected product_template_id in Product Set"))
                vals.append((0, 0, self._get_wiz_line_values(line)))
        self.update({
            "set_line_ids": vals,
        })

    def _get_wiz_line_values(self, set_line):
        return {
            'product_set_line_id': set_line.id,
            'product_variant_ids': [(6, 0, set_line.product_variant_ids.ids)],
            'quantity': set_line.quantity,
            'price' : set_line.price,
            'total_price' : set_line.total_price,
            'product_template_id': set_line.product_template_id.id,
            'sequence': set_line.sequence
        }

    @api.multi
    def add_set(self):
        """Add product set, multiplied by quantity in sale order line."""
        self.ensure_one()
        so_id = self.env.context.get('active_id')
        if not so_id:
            return
        so = self.env['branchwise.material'].browse(so_id)
        max_sequence = 0
        if so.branchwise_material_line_ids:
            max_sequence = max([line.sequence for line in so.branchwise_material_line_ids])
        so_lines = []
        for set_line in self.set_line_ids:
            if not set_line.product_variant_ids:
                variants = set_line.product_template_id.product_variant_ids
                if len(variants) == 1:
                    set_line.product_variant_ids = [(6, 0, variants.ids)]
                else:
                    raise UserError(_("Please select the appropriate product variants for product {}").format(set_line.product_template_id.name))
            for variant in set_line.product_variant_ids:
                so_lines.append((0, 0, self.prepare_sale_order_line_data(so_id,set_line,variant,max_sequence=max_sequence)))
        if so_lines:
            so.write({"branchwise_material_line_ids": so_lines})

    def prepare_sale_order_line_data(self, sale_order_id, set_line, variant, max_sequence=0):
        sale_line = self.env['branchwise.material.line'].new({
                            'from_material_set': 'yes',
                            'material_id': sale_order_id,
                            'product_id': variant.id,
                            'product_uom_qty': set_line.quantity,
                            'price_unit': set_line.price,
                            'product_uom': self.env.ref('product.product_uom_unit').id,
                            'sequence': max_sequence + set_line.sequence,
                        })
        line_values = sale_line._convert_to_write(sale_line._cache)
        return line_values
