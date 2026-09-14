from odoo import models, fields, api
from datetime import datetime

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    lot_id = fields.Many2one('stock.lot',string='Roll Numbers')

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    name = fields.Char(string="Package Name", readonly=True, copy=False,default='New')

    @api.model
    def create(self, vals):

        if not vals.get('name'):
            year = datetime.now().year
            month = datetime.now().month
            month_map = {
                1: 'A', 2: 'B', 3: 'C', 4: 'D',
                5: 'E', 6: 'F', 7: 'G', 8: 'H',
                9: 'I', 10: 'J', 11: 'K', 12: 'L'
            }
            month_code = month_map.get(month)
            seq = self.env['ir.sequence'].next_by_code(
                'stock.quant.package.custom')
            vals['name'] = f"{year}{month_code}{seq}"

        if not vals.get('package_type_id'):
            pallet = self.env['stock.package.type'].search(
                [('name', '=', 'Pallet')], limit=1)
            if pallet:
                vals['package_type_id'] = pallet.id

        return super().create(vals)
