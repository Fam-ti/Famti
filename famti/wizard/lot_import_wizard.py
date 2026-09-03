from odoo import models, fields, _
import base64
import csv
import io
from odoo.exceptions import UserError
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

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
        # required_fields = {'Roll Numbers', 'Quantity'}
        # if not required_fields.issubset(reader.fieldnames):
        #     raise UserError(_("CSV must contain columns: lot_name, qty"))
        imported_rolls = []
        required_fields = {
            'Product',
            'Product Code',
            'Roll Numbers',
            'Quantity',
        }

        if not required_fields.issubset(reader.fieldnames):
            raise UserError(
                _("CSV must contain the following columns:\n%s")
                % ", ".join(sorted(required_fields))
            )
        rows = list(reader)

        Product = self.env['product.product']
        Template = self.env['product.template']

        missing_products = []

        for row in rows:
            csv_product = self._clean_string(row.get('Product'))
            csv_product_code = self._clean_string(row.get('Product Code'))
            roll_number = self._clean_string(row.get('Roll Numbers'))

            if not roll_number:
                continue

            if not csv_product_code:
                missing_products.append(
                    _(
                        "Roll Number: %s\n"
                        "Product: %s\n"
                        "Product Code: Missing"
                    )
                    % (
                        roll_number,
                        csv_product or "N/A",
                    )
                )
                continue

            product = False

            # ============================================================
            # 1. PRODUCT VARIANT - DEFAULT CODE
            # ============================================================

            product = Product.search(
                [
                    ('default_code', '=', csv_product_code),
                ],
                limit=1,
            )

            _logger.info(
                "PRODUCT VARIANT CODE SEARCH | code=%r | result=%s",
                csv_product_code,
                product.ids,
            )

            # ============================================================
            # 2. PRODUCT TEMPLATE - DEFAULT CODE
            # ============================================================

            if not product:

                template = Template.search(
                    [
                        ('default_code', '=', csv_product_code),
                    ],
                    limit=1,
                )

                _logger.info(
                    "PRODUCT TEMPLATE CODE SEARCH | code=%r | result=%s",
                    csv_product_code,
                    template.ids,
                )

                if template:

                    product = template.product_variant_id

                    if not product:
                        product = template.product_variant_ids[:1]

            # ============================================================
            # 3. PRODUCT VARIANT - BARCODE
            # ============================================================

            if not product:
                product = Product.search(
                    [
                        ('barcode', '=', csv_product_code),
                    ],
                    limit=1,
                )

                _logger.info(
                    "PRODUCT BARCODE SEARCH | code=%r | result=%s",
                    csv_product_code,
                    product.ids,
                )

            # ============================================================
            # 4. PRODUCT TEMPLATE - EXACT NAME
            # ============================================================

            if not product and csv_product:

                template = Template.with_context(
                    lang="en_US"
                ).search(
                    [
                        ('name', '=', csv_product),
                    ],
                    limit=1,
                )

                _logger.info(
                    "PRODUCT TEMPLATE NAME SEARCH | name=%r | result=%s",
                    csv_product,
                    template.ids,
                )

                if template:

                    product = template.product_variant_id

                    if not product:
                        product = template.product_variant_ids[:1]

            # ============================================================
            # 5. PRODUCT TEMPLATE - CASE INSENSITIVE NAME
            # ============================================================

            if not product and csv_product:

                template = Template.with_context(
                    lang="en_US"
                ).search(
                    [
                        ('name', 'ilike', csv_product),
                    ],
                    limit=1,
                )

                _logger.info(
                    "PRODUCT TEMPLATE ILIKE SEARCH | name=%r | result=%s",
                    csv_product,
                    template.ids,
                )

                if template:

                    product = template.product_variant_id

                    if not product:
                        product = template.product_variant_ids[:1]

            # ============================================================
            # FINAL PRODUCT DEBUG
            # ============================================================

            if product:

                _logger.info(
                    "PRODUCT FOUND | "
                    "Excel Product=%r | "
                    "Excel Code=%r | "
                    "Product ID=%s | "
                    "Product Name=%r | "
                    "Variant Code=%r | "
                    "Template Code=%r",
                    csv_product,
                    csv_product_code,
                    product.id,
                    product.name,
                    product.default_code,
                    product.product_tmpl_id.default_code,
                )

            else:

                _logger.warning(
                    "PRODUCT NOT FOUND | "
                    "Excel Product=%r | "
                    "Excel Code=%r | "
                    "Roll=%r",
                    csv_product,
                    csv_product_code,
                    roll_number,
                )

                missing_products.append(
                    _(
                        "Roll Number: %s\n"
                        "Product: %s\n"
                        "Product Code: %s"
                    )
                    % (
                        roll_number,
                        csv_product or "N/A",
                        csv_product_code,
                    )
                )

        if missing_products:
            raise ValidationError(
                _(
                    "The following products do not exist in ERP:\n\n%s"
                )
                % "\n\n".join(
                    "- %s" % product
                    for product in missing_products
                )
            )

        move_product = move.product_id

        move_product_name = self._clean_string(
            move_product.name
        )

        move_product_code = self._clean_string(
            move_product.default_code
            or move_product.product_tmpl_id.default_code
        )

        _logger.info(
            "MOVE PRODUCT | "
            "ID=%s | "
            "Name=%r | "
            "Variant Code=%r | "
            "Template Code=%r | "
            "Resolved Code=%r",
            move_product.id,
            move_product_name,
            move_product.default_code,
            move_product.product_tmpl_id.default_code,
            move_product_code,
        )

        matched_rows = []

        for row in rows:

            csv_product = self._clean_string(
                row.get('Product')
            )

            csv_product_code = self._clean_string(
                row.get('Product Code')
            )

            code_match = (
                    bool(csv_product_code)
                    and bool(move_product_code)
                    and csv_product_code.lower()
                    == move_product_code.lower()
            )

            name_match = (
                    not csv_product
                    or csv_product.lower()
                    == move_product_name.lower()
            )

            if code_match and name_match:
                matched_rows.append(row)

                _logger.info(
                    "MOVE PRODUCT MATCHED | "
                    "Product=%r | Code=%r | Roll=%r",
                    csv_product,
                    csv_product_code,
                    row.get('Roll Numbers'),
                )

        if not matched_rows:
            raise ValidationError(
                _(
                    "There was no product match.\n\n"
                    "Selected Product:\n"
                    "Product: %s\n"
                    "Product Code: %s"
                )
                % (
                    move_product_name,
                    move_product_code or "N/A",
                )
            )

        rows = matched_rows
        

        StockLot = self.env['stock.lot']
        StockMoveLine = self.env['stock.move.line']

        processed_lots = set()
        skipped_lots = []
        # rows = list(reader)

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


        missing_suppliers = []

        for row in rows:

            lot_name = self._clean_string(
                row.get('Roll Numbers')
            )

            product = self._clean_string(
                row.get('Product')
            )

            product_code = self._clean_string(
                row.get('Product Code')
            )

            supplier_name = self._clean_string(
                row.get('Supplier name')
            )

            if not supplier_name:
                row['_supplier'] = False
                continue

            supplier = self._find_partner(supplier_name)

            if not supplier:
                missing_suppliers.append(
                    _(
                        "Roll Number: %s\n"
                        "Product: %s\n"
                        "Product Code: %s\n"
                        "Supplier: %s"
                    ) % (
                        lot_name,
                        product,
                        product_code,
                        supplier_name,
                    )
                )
            else:
                row['_supplier'] = supplier


        if missing_suppliers:
            raise ValidationError(
                _(
                    "The following suppliers were not found in system:\n\n%s"
                )
                % "\n\n".join(
                    "- %s" % supplier
                    for supplier in missing_suppliers
                )
            )
        # for row in reader:
        for row in rows:
            product = row.get('Product')
            product_code = row.get('Product Code')
            lot_name = (row.get('Roll Numbers') or '').strip()
            supplier = row.get('_supplier')
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
                'supplier_name': supplier.id if supplier else False,
            })
            imported_rolls.append(lot_name)

        # return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Successful'),
                'message': _(
                    '%s roll(s) imported successfully for product %s.'
                ) % (
                    len(imported_rolls),
                    move_product_name,
                ),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close',
                },
            },
        }

    def _clean_string(self, value):
        if value is None:
            return ""

        return str(value).strip()

    def _map_treatment_in(self, value):

        value = self._clean_string(value)

        if not value:
            return False

        mapping = {

            # CORONA
            "corona": "corona",

            # MET ON CORONA
            "met on corona": "met_corona",
            "met corona": "met_corona",
            "metallized on corona": "met_corona",
            "metallised on corona": "met_corona",

            # MET ON CHEMICAL
            "met on chemical": "met_chemical",
            "met chemical": "met_chemical",
            "metallized on chemical": "met_chemical",
            "metallised on chemical": "met_chemical",

            # MET ON PLAIN
            "met on plain": "met_plain",
            "met plain": "met_plain",
            "metallized on plain": "met_plain",
            "metallised on plain": "met_plain",

            # MET ON COPOLYMER
            "met on copolymer": "met_copolymer",
            "met copolymer": "met_copolymer",
            "metallized on copolymer": "met_copolymer",
            "metallised on copolymer": "met_copolymer",

            # PLAIN
            "plain": "plain",

            # PVDC
            "pvdc": "pvdc",
            "pvdc coated": "pvdc",
            "pvdc coated film": "pvdc",

            # SOFT TOUCH
            "soft touch": "soft_touch",
            "soft-touch": "soft_touch",

            # ALOX
            "alox": "alox",
            "top coat alox": "alox",
            "topcoat alox": "alox",

            # CHEMICAL
            "chemical coated": "chemical_coat",
            "chemical coat": "chemical_coat",
            "chemical coating": "chemical_coat",

            # ACRYLIC
            "acrylic": "acrylic",
            "acrylic coated": "acrylic",

            # COPOLYMER
            "copolymer": "copolymer",
            "co-polymer": "copolymer",
            "co polymer": "copolymer",

            # SPECIAL CHEMICAL
            "special chemical": "special_chemical",
            "special chemical coated": "special_chemical",
            "special chemical coating": "special_chemical",
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

            # CORONA
            "corona": "corona",

            # MET ON CORONA
            "met on corona": "met_corona",
            "met corona": "met_corona",
            "metallized on corona": "met_corona",
            "metallised on corona": "met_corona",

            # MET ON CORONA - OUTSIDE
            "metallized on corona outside": "met_corona_out",
            "metallised on corona outside": "met_corona_out",
            "met corona outside": "met_corona_out",

            # MET ON CHEMICAL
            "met on chemical": "met_chemical",
            "met chemical": "met_chemical",
            "metallized on chemical": "met_chemical",
            "metallised on chemical": "met_chemical",

            # MET ON PLAIN
            "met on plain": "met_plain",
            "met plain": "met_plain",
            "metallized on plain": "met_plain",
            "metallised on plain": "met_plain",

            # MET ON COPOLYMER
            "met on copolymer": "met_copolymer",
            "met copolymer": "met_copolymer",
            "metallized on copolymer": "met_copolymer",
            "metallised on copolymer": "met_copolymer",

            # PLAIN
            "plain": "plain",

            # PVDC
            "pvdc": "pvdc_out",
            "pvdc coated": "pvdc_out",
            "pvdc coated film": "pvdc_out",

            # ACRYLIC
            "acrylic": "acrylic",
            "acrylic coated": "acrylic",

            # COPOLYMER
            "copolymer": "copolymer",
            "co-polymer": "copolymer",
            "co polymer": "copolymer",

            # SOFT TOUCH
            "soft touch": "soft_touch",
            "soft-touch": "soft_touch",

            # ALOX
            "alox": "alox",
            "top coat alox": "alox",
            "topcoat alox": "alox",

            # CHEMICAL
            "chemical coated": "chemical_coat",
            "chemical coat": "chemical_coat",
            "chemical coating": "chemical_coat",

            # SPECIAL CHEMICAL
            "special chemical": "special_chemical",
            "special chemical coated": "special_chemical",
            "special chemical coating": "special_chemical",
        }

        result = mapping.get(value.lower())

        if result is None:
            raise ValidationError(
                _("Invalid Treatment OUT value: %s") % value
            )

        return result

    def _find_partner(self, supplier_name):
        supplier_name = self._clean_string(supplier_name)

        if not supplier_name:
            return False

        supplier = self.env['res.partner'].search([
            ('name', '=', supplier_name),
        ], limit=1)

        if supplier:
            return supplier

        supplier = self.env['res.partner'].search([
            ('name', '=ilike', supplier_name),
        ], limit=1)

        return supplier
