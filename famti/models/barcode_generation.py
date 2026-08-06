from odoo import models, fields, api
import re
from odoo.exceptions import ValidationError


class BarcodeGeneration(models.Model):
    _name = 'barcode.generation'
    _description = 'Barcode Generation'

    name = fields.Char(
        string="Reference",
        required=True
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product"
    )

    pallet_id = fields.Many2one(
        'stock.quant.package',
        string="Pallet"
    )

    pallet_number = fields.Char(string="Pallet Number")

    serial_start = fields.Char(
        string="Serial Number Start",
    )

    serial_end = fields.Char(
        string="Serial Number End",
        readonly=True
    )

    total_sequence = fields.Integer(
        string="Total Sequence",
        required=True
    )

    line_ids = fields.One2many(
        'barcode.generation.line',
        'barcode_generation_id',
        string="Generated Lines"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated')
    ], default='draft')

    def action_generate(self):
        for rec in self:
            rec.line_ids.unlink()

            # match = re.match(r'([A-Za-z]+)(\d+)', rec.serial_start)
            match = re.match(r'^(.*?)(\d+)$', rec.serial_start.strip())
            if not match:
                raise ValidationError("Invalid Serial Start Format")

            prefix = match.group(1)
            start_num = int(match.group(2))
            padding = len(match.group(2))

            end_num = start_num + rec.total_sequence - 1
            rec.serial_end = f"{prefix}{str(end_num).zfill(padding)}"

            lines = []

            for i in range(rec.total_sequence):
                serial = f"{prefix}{str(start_num + i).zfill(padding)}"

                # existing_lot = self.env['stock.lot'].search([
                #     ('name', '=', serial)
                # ], limit=1)

                # if existing_lot:
                #     lot = existing_lot
                # else:
                #     lot = self.env['stock.lot'].create({
                #         'name': serial,
                #         'product_id': rec.product_id.id,
                #     })

                lines.append((0, 0, {
                    'product_id': rec.product_id.id,
                    # 'pallet_id': rec.pallet_id.id,
                    # 'serial_number_id': lot.id,
                    'pallet_number': rec.pallet_number,
                    'serial_number': serial,
                    'barcode_value': serial,
                }))

            rec.line_ids = lines
            rec.state = 'generated'



class BarcodeGenerationLine(models.Model):
    _name = 'barcode.generation.line'
    _description = 'Barcode Generation Line'

    barcode_generation_id = fields.Many2one(
        'barcode.generation'
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product"
    )

    pallet_id = fields.Many2one(
        'stock.quant.package',
        string="Pallet"
    )

    pallet_number = fields.Char(string="Pallet Number")

    serial_number_id = fields.Many2one(
        'stock.lot',
        string="Serial Number"
    )

    serial_number = fields.Char(string="Serial Number")

    barcode_value = fields.Char(
        string="Barcode"
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_generate_barcodes(self):
        lines = []

        for picking in self:
            print("Receipt:", picking.name)

            for move in picking.move_ids_without_package:
                package = move.product_packaging_id.name if move.product_packaging_id else "No Package"

                if move.lot_ids:
                    for lot in move.lot_ids:
                        lines.append({
                            'product_name': move.product_id.display_name,
                            'serial_number': lot.name,
                            'package_number': package,
                            'barcode_value': lot.name,
                        })

                else:
                    lines.append({
                        'product_name': move.product_id.display_name,
                        'serial_number': '',
                        'package_number': package,
                        'barcode_value': move.product_id.barcode or '',
                    })

        return self.env.ref(
            'famti.action_report_receipt_barcode'
        ).report_action(self, data={'lines': lines})
    

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_print_serial_barcodes(self):
        lines = []

        for production in self:
            print("MO:", production.name)

            for line in production.serial_line_ids:
                lines.append({
                    'product_name': line.po_product_code,
                    'serial_number': line.serial_number,
                    'barcode_value': line.serial_number,
                })

        return self.env.ref(
            'famti.action_report_mrp_barcode'
        ).report_action(self, data={'lines': lines})
    
class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_print_lot_barcodes(self):
        lines = []

        for lot in self:
            lines.append({
                'product_name': lot.product_id.display_name,
                'serial_number': lot.name,
                'pallet_number': lot.pallet_no or '',
                'barcode_value': lot.name,
            })

        return self.env.ref(
            'famti.action_report_lot_barcode'
        ).report_action(self, data={'lines': lines})
    
class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def action_print_package_barcodes(self):
        lines = []

        for package in self:
            for quant in package.quant_ids:
                lines.append({
                    'product_name': quant.product_id.display_name,
                    'serial_number': quant.lot_id.name if quant.lot_id else '',
                    'package_number': package.name,
                    'barcode_value': quant.lot_id.name if quant.lot_id else package.name,
                })

        return self.env.ref(
            'famti.action_report_package_barcode'
        ).report_action(self, data={'lines': lines})
