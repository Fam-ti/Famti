from odoo import models, fields, _
import base64
import csv
import io
from odoo.exceptions import UserError
from odoo.exceptions import UserError, ValidationError


class FamtiLotImportWizard(models.TransientModel):
    _name = "famti.lot.import.wizard"
    _description = "Import Lots from Excel/CSV"

    file = fields.Binary(string="File", required=True)
    filename = fields.Char()

    def action_import(self):
        self.ensure_one()

        move = self.env['stock.move'].browse(self.env.context.get('active_id'))
        if not move:
            raise UserError(_("No stock move found."))

        if move.product_id.tracking == 'none':
            raise UserError(_("Product is not tracked by lot/serial."))

        move.move_line_ids.filtered(
            lambda l: not l.quantity or l.state != 'done'
        ).unlink()

        try:
            data = base64.b64decode(self.file)
            file_io = io.StringIO(data.decode('utf-8-sig'))
            reader = csv.DictReader(file_io)
        except Exception:
            raise UserError(_("Invalid CSV file."))

        # required_fields = {'lot_name', 'qty'}
        required_fields = {'Roll Numbers', 'Quantity'}
        if not required_fields.issubset(reader.fieldnames):
            raise UserError(_("CSV must contain columns: lot_name, qty"))

        StockLot = self.env['stock.lot']
        StockMoveLine = self.env['stock.move.line']

        processed_lots = set()
        skipped_lots = []
        rows = list(reader)

        roll_numbers = []
        duplicate_rolls = set()
        seen_rolls = set()

        for row in rows:
            lot_name = (row.get('Roll Numbers') or '').strip()

            if not lot_name:
                continue

            if lot_name in seen_rolls:
                duplicate_rolls.add(lot_name)

            seen_rolls.add(lot_name)
            roll_numbers.append(lot_name)

        if duplicate_rolls:
            raise ValidationError(
                _("Duplicate Roll Numbers found in CSV:\n\n%s")
                % "\n".join(
                    "- %s" % x for x in sorted(duplicate_rolls)
                )
            )


        existing_lots = StockLot.search([
            ('name', 'in', roll_numbers),
            ('product_id', '=', move.product_id.id),
        ])

        if existing_lots:
            existing_rolls = existing_lots.mapped('name')

            raise ValidationError(
                _("The following Roll Numbers already exist for product '%s':\n\n%s")
                % (
                    move.product_id.display_name,
                    "\n".join(
                        "- %s" % x for x in sorted(existing_rolls)
                    )
                )
            )
        # for row in reader:
        for row in rows:
            product = row.get('Product')
            product_code = row.get('Product Code')
            lot_name = (row.get('Roll Numbers') or '').strip()
            supplier_name = row.get('Supplier name')
            film_type = row.get('Film Type')
            type_value = row.get('Type')
            film_description = row.get('Film Description')
            # treatment_in = row.get('Treatment IN')
            # treatment_out = row.get('Treatment OUT')
            treatment_in_excel = row.get('Treatment IN')
            treatment_out_excel = row.get('Treatment OUT')

            treatment_in = self._map_treatment_in(treatment_in_excel)
            treatment_out = self._map_treatment_out(treatment_out_excel)
            pallet_number = row.get('Pallet Number')
            thickness = row.get('Thickness')
            thickness_uom = row.get('Thickness UOM')
            width = row.get('Width')
            width_uom = row.get('Width UOM')
            weight = row.get('Weight')
            weight_uom = row.get('Weight UOM')

            quantity_value = row.get('Quantity')
            pallet_number = (row.get('Pallet Number') or '').strip()

            package = False

            if pallet_number:
                package = self.env['stock.quant.package'].search([
                    ('name', '=', pallet_number),
                ], limit=1)

                if not package:
                    package = self.env['stock.quant.package'].create({
                        'name': pallet_number,
                    })

            try:
                qty = float(quantity_value or 0)
            except (ValueError, TypeError):
                raise UserError(
                    _("Invalid Quantity '%s' in Excel row.") % quantity_value
                )

            quantity_uom = row.get('Quantity UOM')
            # length = row.get('Length')
            length = float(
                    str(row.get('Length') or 0).replace(',', '').strip()
                )
            length_uom = row.get('Length UOM')
            received_date = row.get('Received date')
            aging = row.get('Aging')
            core_id = row.get('Core Id')
            no_of_joint = row.get('no_of_joint')

            if not lot_name or qty <= 0:
                continue


            if lot_name in processed_lots:
                skipped_lots.append(lot_name)
                continue
            processed_lots.add(lot_name)

            existing_move_lines = StockMoveLine.search([
                ('move_id', '=', move.id),
                ('lot_name', '=', lot_name),
            ])

            if existing_move_lines:
                print(
                    existing_move_lines.ids
                )

                existing_move_lines.unlink()

            # lot = StockLot.search([
            #     ('name', '=', lot_name),
            #     ('product_id', '=', move.product_id.id),
            #     '|',
            #     ('company_id', '=', move.company_id.id),
            #     ('company_id', '=', False),
            # ], limit=1)

            # # if lot:
            # #     print("====already exit")
            # #     skipped_lots.append(lot_name)
            # #     continue

            # # lot = StockLot.create({
            # #     'name': lot_name,
            # #     'product_id': move.product_id.id,
            # #     'company_id': move.company_id.id,
            # # })
            # if lot:
            #     existing_move_lines = StockMoveLine.search([
            #         ('move_id', '=', move.id),
            #         ('lot_id', '=', lot.id),
            #     ])

            #     if existing_move_lines:
            #         existing_move_lines.unlink()

            # else:
            #     lot = StockLot.create({
            #         'name': lot_name,
            #         'product_id': move.product_id.id,
            #         'company_id': move.company_id.id,
            #     })

            StockMoveLine.create({
                'move_id': move.id,
                'lot_name': lot_name,
                'film': type_value,
                'film_type': film_type,
                'thickness': thickness,
                'weight': weight,
                'weight_uom':weight_uom,
                'core_id': core_id,
                # 'category': category,
                # 'lot_number': lot_number,
                'pallet_no': pallet_number,
                'result_package_id': package.id if package else False,
                'picking_id': move.picking_id.id,
                'product_id': move.product_id.id,
                'quantity': qty,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'treatment_in': treatment_in,
                'treatment_out': treatment_out,
                'width': width,
                'width_uom':width_uom,
                'length':length,
                'length_uom':length_uom,
                'description':film_description,
            })

        return {'type': 'ir.actions.act_window_close'}

    def _clean_string(self, value):
        if value is None:
            return ""

        return str(value).strip()


    def _map_treatment_in(self, value):

        value = self._clean_string(value)

        if not value:
            return False

        mapping = {
            "corona": "corona",
            "met on corona": "met_corona",
            "met corona": "met_corona",
            "met on chemical": "met_chemical",
            "met chemical": "met_chemical",
            "met on plain": "met_plain",
            "met plain": "met_plain",
            "plain": "plain",
            "pvdc coated": "pvdc",
            "pvdc": "pvdc",
            "soft touch": "soft_touch",
            "top coat alox": "alox",
            "alox": "alox",
        }

        result = mapping.get(value.lower())

        if result is None:
            raise ValidationError(
                _("Invalid Treatment IN value: %s") % value
            )

        return result


    def _map_treatment_out(self, value):

        value = self._clean_string(value)

        if not value:
            return False

        mapping = {
            "acrylic": "acrylic",
            "corona": "corona",
            "met on plain": "met_plain",
            "met plain": "met_plain",
            "met on corona": "met_corona",
            "met corona": "met_corona",
            "metallized on corona outside": "met_corona_out",
            "met corona outside": "met_corona_out",
            "metallized on chemical": "met_chemical",
            "met chemical": "met_chemical",
            "plain": "plain",
            "pvdc coated": "pvdc_out",
            "pvdc": "pvdc_out",
        }

        result = mapping.get(value.lower())

        if result is None:
            raise ValidationError(
                _("Invalid Treatment OUT value: %s") % value
            )

        return result
