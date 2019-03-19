import odoo.addons.decimal_precision as dp
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class UniformSetAdd(models.TransientModel):
	_name = 'uniform.set.add'
	_rec_name = 'product_set_id'

	product_set_id = fields.Many2one('uniform.set', string='Uniform Set')
	quantity = fields.Float(string='Quantity', digits=dp.get_precision('Uniform Unit of Measure'), default=1)
	set_line_ids = fields.One2many('uniform.set.add.line', 'wizard_id', string='Uniform Set Add Line')

	@api.onchange('product_set_id')
	def _onchange_product_set_id(self):
		vals = []
		if self.product_set_id:
			for line in self.product_set_id.uniform_set_item_ids:
				if not line.product_template_id:
					raise ValidationError(_("No selected Uniform Items in Uniform Set"))
				vals.append((0, 0, self._get_wizard_line_values(line)))
		self.update({"set_line_ids": vals})

	def _get_wizard_line_values(self, set_line):
		return {
			'product_set_line_id': set_line.id,
			'product_variant_ids': [(6, 0, set_line.product_variant_ids.ids)],
			'quantity': set_line.quantity,
			'product_template_id': set_line.product_template_id.id,
			'sequence': set_line.sequence
		}

	@api.multi
	def add_set(self):
		"""Add Uniform set, multiplied by quantity in Uniform items."""
		self.ensure_one()
		admission = self.env.context.get('active_id')
		if not admission:
			return
		admission_id = self.env['pappaya.admission'].browse(admission)
		max_sequence = 0
		if admission_id.uniform_set_ids:
			max_sequence = max([line.sequence for line in admission_id.uniform_set_ids])
		lines = []
		for set_line in self.set_line_ids:
			if not set_line.product_variant_ids:
				variants = set_line.product_template_id.product_variant_ids
				if len(variants) == 1:
					set_line.product_variant_ids = [(6, 0, variants.ids)]
				else:
					raise UserError(_("Please select the appropriate Uniform Variant for Uniform items {}").format(
																				set_line.product_template_id.name))
			for variant in set_line.product_variant_ids:
				lines.append(
					(0, 0, self.prepare_sale_order_line_data(admission, set_line, variant, max_sequence=max_sequence)))
		if lines:
			admission_id.write({"uniform_set_ids": lines})

	def prepare_sale_order_line_data(self, sale_order_id, set_line, variant, max_sequence=0):
		sale_line = self.env['admission.uniform'].new({
			'from_uniform_set': 'yes',
			'admission_id': sale_order_id,
			'product_id': variant.id,
			'product_uom_qty': self.quantity,
			'product_uom': self.env.ref('product.product_uom_unit').id,
			'sequence': max_sequence + set_line.sequence,
		})
		line_values = sale_line._convert_to_write(sale_line._cache)
		return line_values


class UniformSetAddLine(models.TransientModel):
	_name = 'uniform.set.add.line'
	_order = 'sequence'

	wizard_id = fields.Many2one('uniform.set.add', string="Uniform Set Add")
	product_set_line_id = fields.Many2one('uniform.item', string="Uniform Item")
	product_set_id = fields.Many2one('uniform.set', string='Uniform Set', related='product_set_line_id.product_set_id')
	sequence = fields.Integer(string='Sequence')
	product_template_id = fields.Many2one('product.template', string='Uniform Item')
	product_variant_ids = fields.Many2many('product.product',
										domain="""['&',('sale_ok', '=', True),
										('product_tmpl_id', '=', product_template_id),]""", string='Variant')
	quantity = fields.Float(string='Quantity', digits=dp.get_precision('Uniform Unit of Measure'))

	@api.onchange('product_template_id')
	def _onhange_product_template_id(self):
		for record in self:
			variants = record.product_template_id.product_variant_ids
			if len(variants) == 1:
				record.product_variant_ids = [(6, 0, variants.ids)]
			else:
				record.product_variant_ids = [(5, 0, 0)]
