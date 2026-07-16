from odoo import models, fields


class BarcodeLabelWizard(models.TransientModel):
    _name = 'barcode.label.wizard'
    _description = 'Barcode Label Wizard'

    barcode_generation_id = fields.Many2one(
        'barcode.generation'
    )

    copies = fields.Integer(
        string="Copies",
        default=1,
        required=True
    )

    print_format = fields.Selection([
        ('dymo', 'Dymo'),
        ('4x7', '4 x 7'),
        ('4x12', '4 x 12'),
        ('2x7', '2 x 7'),
        ('3x8', '3 x 8'),
        ('5x10', '5 x 10'),
    ], string="Format", default="dymo", required=True)


    def action_print(self):
        self.ensure_one()

        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])

        records = self.env[active_model].browse(active_ids)

        if active_model == 'barcode.generation':
            return self.env.ref(
                'famti.action_report_barcode_labels'
            ).with_context(
                copies=self.copies,
                print_format=self.print_format
            ).report_action(records)

        elif active_model == 'stock.lot':
            lines = []

            for lot in records:
                lines.append({
                    'product_name': lot.product_id.display_name,
                    'serial_number': lot.name,
                    'pallet_number': lot.pallet_no or '',
                    'barcode_value': lot.name,
                })

            return self.env.ref(
                'famti.action_report_lot_barcode'
            ).with_context(
                copies=self.copies,
                print_format=self.print_format
            ).report_action(records, data={'lines': lines})

        elif active_model == 'stock.quant.package':
            lines = []

            for package in records:
                for quant in package.quant_ids:
                    lines.append({
                        'product_name': quant.product_id.display_name,
                        'serial_number': quant.lot_id.name if quant.lot_id else '',
                        'package_number': package.name,
                        'barcode_value': quant.lot_id.name if quant.lot_id else package.name,
                    })

            return self.env.ref(
                'famti.action_report_package_barcode'
            ).with_context(
                copies=self.copies,
                print_format=self.print_format
            ).report_action(records, data={'lines': lines})

        elif active_model == 'stock.picking':
            lines = []

            for picking in records:
                for move in picking.move_ids_without_package:
                    package = move.product_packaging_id.name if move.product_packaging_id else ''

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
            ).with_context(
                copies=self.copies,
                print_format=self.print_format
            ).report_action(records, data={'lines': lines})

        elif active_model == 'mrp.production':
            lines = []

            for production in records:
                for serial_line in production.serial_line_ids:
                    lines.append({
                        'product_name': production.product_id.display_name,
                        'serial_number': serial_line.serial_number or '',
                        'pallet_number': serial_line.po_product_code or '',
                        'barcode_value': serial_line.serial_number or '',
                    })

            return self.env.ref(
                'famti.action_report_mrp_barcode'
            ).with_context(
                copies=self.copies,
                print_format=self.print_format
            ).report_action(records, data={'lines': lines})
    