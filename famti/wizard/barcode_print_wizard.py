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
        ('single', 'Single'),
        ('dymo', 'Dymo'),
        ('2x2', '2 x 2'),
    ], string="Format", default="single", required=True)


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
                    'thickness': lot.thickness,
                    'thickness_uom': lot.thickness_uom,
                    'width': lot.width_val,
                    'width_uom': lot.width_uom,
                    'weight': lot.weight,
                    'length': lot.length_val,
                    'length_uom': lot.length_uom,
                    'treatment_in': dict(lot._fields['treatment_in'].selection).get(lot.treatment_in, ''),
                    'treatment_out': dict(lot._fields['treatment_out'].selection).get(lot.treatment_out, ''),
                    'product': lot.product_id.name,
                    'po_product_code': lot.mo_product_code,
                    'date': lot.create_date,
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

            # for picking in records:
            #     for move in picking.move_ids_without_package:
            #         package = move.product_packaging_id.name if move.product_packaging_id else ''

            #         if move.lot_ids:
            #             for lot in move.lot_ids:
            #                 lines.append({
            #                     'product_name': move.product_id.display_name,
            #                     'serial_number': lot.name,
            #                     'package_number': package,
            #                     'barcode_value': lot.name,
            #                 })
            #         else:
            #             lines.append({
            #                 'product_name': move.product_id.display_name,
            #                 'serial_number': '',
            #                 'package_number': package,
            #                 'barcode_value': move.product_id.barcode or '',
            #             })

            for picking in records:
                for move in picking.move_ids_without_package:
                    package = move.product_packaging_id.name if move.product_packaging_id else ''

                    # Automatically detect PO or SO source
                    if move.purchase_line_id:
                        order_line = move.purchase_line_id
                    elif move.sale_line_id:
                        order_line = move.sale_line_id
                    else:
                        order_line = False

                    order = order_line.order_id if order_line else False

                    spec_vals = {
                        'thickness': getattr(order_line, 'thickness_val', '') if order_line else '',
                        'thickness_uom': getattr(order_line, 'thickness_uom', '') if order_line else '',
                        'width': getattr(order_line, 'width_val', '') if order_line else '',
                        'width_uom': getattr(order_line, 'width_uom', '') if order_line else '',
                        'length': getattr(order_line, 'length_val', '') if order_line else '',
                        'length_uom': getattr(order_line, 'length_uom', '') if order_line else '',
                        'treatment_in': dict(order_line._fields['treatment_in'].selection).get(order_line.treatment_in, order_line.treatment_in) if order_line and order_line.treatment_in else '',
                        'treatment_out': dict(order_line._fields['treatment_out'].selection).get(order_line.treatment_out, order_line.treatment_out) if order_line and order_line.treatment_out else '',
                        'product': getattr(order_line.product_id, 'name', '') if order_line and order_line.product_id else '',
                        'po_product_code': order.name if order else '',
                        'date': order.date_order if order else picking.scheduled_date,
                    }

                    if move.lot_ids:
                        for lot in move.lot_ids:
                            lines.append({
                                'product_name': move.product_id.display_name,
                                'serial_number': lot.name,
                                'package_number': package,
                                'barcode_value': lot.name,
                                'quantity': move.quantity,
                                'uom_id': move.product_uom.name,
                                **spec_vals,
                            })
                    else:
                        lines.append({
                            'product_name': move.product_id.display_name,
                            'serial_number': '',
                            'package_number': package,
                            'barcode_value': move.product_id.barcode or '',
                            'quantity': move.quantity,
                            'uom_id': move.product_uom.name,
                            **spec_vals,
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
                    # lines.append({
                    #     'product_name': production.product_id.display_name,
                    #     'serial_number': serial_line.serial_number or '',
                        
                    #     'barcode_value': serial_line.serial_number or '',
                    # })
                    lines.append({
                        'product_name': serial_line.mo_product_code,
                        'serial_number': serial_line.serial_number,
                        'pallet_number': serial_line.po_product_code or '',
                        'barcode_value': serial_line.serial_number,
                        'thickness': serial_line.thickness,
                        'thickness_uom': serial_line.thickness_uom,
                        'width': serial_line.width,
                        'width_uom': serial_line.width_uom,
                        'length': serial_line.length,
                        'length_uom': serial_line.length_uom,
                        'quantity': serial_line.quantity,
                        'uom_id': serial_line.uom_id.name,
                        'grade_type': serial_line.grade_type,
                        'treatment_in': dict(serial_line._fields['treatment_in'].selection).get(serial_line.treatment_in, ''),
                        'treatment_out': dict(serial_line._fields['treatment_out'].selection).get(serial_line.treatment_out, ''),
                        'po_product_code': serial_line.po_product_code,
                        'date': serial_line.create_date,
                        'product': production.product_id.name,
                        'mo_number': production.name,
                    })

            return self.env.ref(
                'famti.action_report_mrp_barcode'
            ).with_context(
                copies=self.copies,
                print_format=self.print_format
            ).report_action(records, data={'lines': lines})
    
