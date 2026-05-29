from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from datetime import date
from io import BytesIO
import base64
import xlsxwriter

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    serial_line_ids = fields.One2many('mrp.production.serial.line', 'production_id',
        string='Serial Details'
    )
    scrap_line_ids = fields.One2many('mrp.production.scrap.line','production_scrap_id', string='Scrap Details')

    mo_serial_no = fields.Boolean( related='product_id.mo_serial_no',
        store=False
    )

    is_slitting = fields.Boolean(string="Slitting")

    scrap_location_id = fields.Many2one('stock.location',string='Scrap Location',
        domain=[('scrap_location', '=', True)],
    )

    consumable_line_ids = fields.One2many('mrp.consumables','production_id',
        string='Consumables'
    )

    product_code =fields.Char(string="Product Code")

    raw_material_move_ids = fields.One2many(
        'stock.move',
        'raw_material_production_id',
        domain=[('product_id.is_consumables', '=', False)],
        string="Raw Materials"
    )

    consumable_move_ids = fields.One2many(
        'stock.move',
        'raw_material_production_id',
        domain=[('product_id.is_consumables', '=', True)],
        string="Consumables"
    )
    logo = fields.Image("Logo", max_width=1920, max_height=1920, default=lambda self: self.env.company.logo)

    def generate_oil_grease_lubrication_xlsx(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Lubrication Sheet')


        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'align': 'center',
            'text_wrap': True,
        })

        normal_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top',
        })

        center_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        # Column Widths
        sheet.set_column('A:A', 45)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:J', 10)

        # Title

        sheet.merge_range(
            'A1:J1',
            'OIL / GREASE LUBRICATION FOR SLITTING',
            title_format
        )
        # Headers
        headers = [
            'Equipment',
            'Oil/Grease Type',
            'D',
            'W',
            'M',
            'Q',
            'BA',
            'A',
            '2 YEARS',
        ]

        row = 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1
        # Static Data
        data = [
            ['HYDRULIC OIL', 'LHM 46', '', '', '', '', '', '', 'X'],

            ['unwinding brackets (left and right)', 'LCKC 220', '', '', '', '', '', 'X', ''],

            ['Unwinding chucks left and right', 'LCKC 220', '', '', '', '', 'X', '', ''],

            ['When swinging, the oil filling hole on the linear guide for the horizontal movement of the screw tighten unit',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['the Screwstroke drive for the horizontal movement of unwinding bracket',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['the oil filling hole on the horizontal movement of unwinder bracket (left and right)',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['The gear driver on the motor for the swing of unwinding bracket (The gear driver is lifelong lubricated)',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['The oil filling hole of bearing system for oscillation of unwinding bracket',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['The oil filling point on linear guide for horizontal bracket (left and right)',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['The oil filling point on linear guide for horizontal movement of sliding rail for unloading core (left and right)',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['End gear reduction drive motor for the oscillation of scanning sensor',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['gear reduction drive motor of film',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['threading mechanism',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['chain of film threading mechanism',
             'SAE30', '', '', '', '', '', '', 'X'],

            ['banana roll',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['gear reduction drive motor for adjustment of banana roll drive',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['guiding roll and pneumatic spring brake disc on bottom knife shaft',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['Planetary gear driver for automatically adjusted knife holder',
             'LCKC 220', '', '', '', '', '', 'X', ''],

            ['The oil filling point on linear guides for horizontal movement of rewinding beam',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['The oil filling point on spiral bevel gear for rewinding AC servo motor',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['gear reduction drive motor of rewinder',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['rewinding chuck',
             'LCKC 220', '', '', '', '', '', '', 'X'],

            ['unwinding chuck',
             'NLGL-2', '', '', '', '', '', '', 'X'],

            ['LINEAR GUIDE',
             'NLGL-2', '', '', 'X', '', '', '', ''],

            ['SCREW',
             'NLGL-2', '', '', 'X', '', '', '', ''],

            ['BEARING',
             'NLGL-2', '', '', 'X', '', '', '', ''],

            ['STAR GEAR',
             'VG68', '', '', '', '', '', 'X', ''],

            ['rewinding chuck',
             'NLGL-2', '', '', '', '', '', 'X', ''],
        ]

        for item in data:

            col = 0

            for value in item:
                sheet.write(row, col, value, normal_format)
                col += 1

            row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Oil_Grease_Lubrication.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype':
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    @api.onchange('product_id')
    def _onchange_product_id_set_code(self):
        for rec in self:
            if rec.product_id:
                rec.product_code = rec.product_id.default_code
            else:
                rec.product_code = False

    # @api.onchange('product_qty')
    # def _onchange_create_raw_move(self):
    #     for rec in self:
    #         if rec.product_qty > 0:
    #             rec.move_raw_ids = [(5, 0, 0)]
    #             rec.move_raw_ids = [(0, 0, {
    #                 'product_uom_qty': rec.product_qty,
    #             })]

    @api.model
    def create(self, vals):
        if vals.get('origin'):
            vals['bom_id'] = False

        return super().create(vals)

    def action_confirm(self):
        for rec in self:
            for move in rec.move_raw_ids:
                if move.product_uom_qty <= 0:
                    move.product_uom_qty = rec.product_qty
                    # raise ValidationError(
                    #     f"Raw Material '{move.product_id.display_name}' must have a quantity greater than 0."
                    # )
        for record in self:
            for move in record.move_raw_ids:
                product = move.product_id

                available_qty = product.with_context(
                    location=move.location_id.id
                ).qty_available

                if available_qty < move.product_uom_qty:
                    raise ValidationError(_(
                        "Not enough stock for product: %s\n"
                        "Required: %s\nAvailable: %s"
                    ) % (
                        product.display_name,
                        move.product_uom_qty,
                        available_qty
                    ))
                
        return super().action_confirm()


    def _prepare_stock_lot_values(self):
        self.ensure_one()

        name = self.env['stock.lot']._get_next_serial(
            self.company_id,
            self.product_id
        )

        return {
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'name': name,
        }


    def action_generate_serial(self):
        wc = self.workorder_ids[:1].workcenter_id
        ctx = dict(self.env.context)

        not_done_workorders = self.workorder_ids.filtered(
            lambda wo: wo.state != 'done'
        )

        if not_done_workorders:
            names = ", ".join(not_done_workorders.mapped('name'))
            raise ValidationError(
                _("You cannot split lots.\n"
                "The following Work Orders are not Done: %s") % names
            )

        if wc and wc.code:
            ctx['machine_code'] = wc.code

        res = super(MrpProduction, self.with_context(ctx)).action_generate_serial()

        for production in self:
            if production.lot_producing_id:

                production.serial_line_ids.unlink()

                self.env['mrp.production.serial.line'].create({
                    'production_id': production.id,
                    'serial_number': production.lot_producing_id.name,
                    'location_id': production.location_dest_id.id,
                    'quantity': production.qty_producing,
                    'uom_id': production.product_uom_id.id,
                    'total_input': production.product_qty,
                    'mo_product_code':production.product_code,
                    'po_product_code': production.move_raw_ids[-1].product_id.default_code
                })

        return res


    def action_open_split_lots_wizard(self):
        self.ensure_one()
        not_done_workorders = self.workorder_ids.filtered(
            lambda wo: wo.state != 'done'
        )

        if not_done_workorders:
            names = ", ".join(not_done_workorders.mapped('name'))
            raise ValidationError(
                _("You cannot split lots.\n"
                "The following Work Orders are not Done: %s") % names
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Split Lots',
            'res_model': 'mrp.batch.produce',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            }
        }

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        self.bom_id = False

        return res


    def action_open_scrap_wizard(self):
        self.ensure_one()

        Wizard = self.env['mrp.production.scrap.wizard']
        WizardLine = self.env['mrp.production.scrap.wizard.line']

        wizard = Wizard.create({
            'production_id': self.id,
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'date': fields.Datetime.now(),
            'location_id':self.location_dest_id.id,
            'scrap_location_id':self.scrap_location_id.id,
        })

        if self.lot_producing_id:
            lot = self.lot_producing_id
            WizardLine.create({
                'wizard_id': wizard.id,
                'serial_number_id': lot.id,
                'serial_number': lot.name,
                'available_qty': self.qty_producing,
                'uom_id': self.product_uom_id.id,
            })
        else:
            for move in self.serial_line_ids:
                WizardLine.create({
                    'wizard_id': wizard.id,
                    'serial_line_id': move.id,
                    'serial_number': move.serial_number,
                    'available_qty': move.quantity,
                    'uom_id': move.uom_id.id,
                    'location_id': move.location_id.id,
                    'thickness': move.thickness,
                    'thickness_uom': move.thickness_uom,
                    'width': move.width,
                    'width_uom': move.width_uom,
                    'core_id': move.core_id,
                    'length': move.length,
                    'length_uom': move.length_uom,
                    'recived': move.recived,
                    'billed': move.billed,
                    'film_category': move.film_category,
                    'film': move.film,
                    'film_type': move.film_type,
                })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Scrap Before Production',
            'res_model': 'mrp.production.scrap.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }


    @api.constrains('serial_line_ids')
    def _check_lot_quantity(self):
        for mo in self:
            if not mo.serial_line_ids:
                continue
            total = sum(mo.serial_line_ids.mapped('quantity'))
            if float_compare(
                total,
                mo.product_qty,
                precision_rounding=mo.product_uom_id.rounding
            ) != 0:
                raise ValidationError(
                    "Total lot quantities must equal Manufacturing Order quantity."
                )

    def button_mark_done(self):
        failed_lots=[]
        for mo in self:
            if mo.move_raw_ids:
                for prod in mo.move_raw_ids:
                    for lot in prod.lot_ids:
                            if lot.qc_status in ['pending','failed']:
                                failed_lots.append(lot.name)
            if failed_lots:
                raise UserError(
                    f"The following Lots are not QC Approved:\n{', '.join(failed_lots)}"
                )

            not_done_workorders = self.workorder_ids.filtered(
                lambda wo: wo.state != 'done'
            )

            if not_done_workorders:
                names = ", ".join(not_done_workorders.mapped('name'))
                raise ValidationError(
                    _("You cannot split lots.\n"
                    "The following Work Orders are not Done: %s") % names
                )

            for rec in mo.serial_line_ids:

                fields_to_check = {
                    'Thickness': rec.thickness,
                    'Width': rec.width,
                    'Length': rec.length,
                }

                for label, value in fields_to_check.items():
                    if not rec.total_scrap or rec.total_scrap == 0:
                        if value <= 0:
                            raise ValidationError(
                                _("Serial %s: Please Enter the value for  %s .")
                                % (rec.serial_number or '', label)
                            )
            density = 0
            raw_move = mo.move_raw_ids.filtered(lambda m: m.product_id)[:1]
            if raw_move:
                density = raw_move.product_id.density or 0

            for rec in mo.serial_line_ids:
                calculated_weight = 0
                if rec.thickness and rec.width and rec.length and density:
                    calculated_weight = (
                        rec.thickness * rec.width * rec.length * density
                    ) / 1000000
                    print("calculated_weight---------",calculated_weight)
                    print("rec.recived---------",rec.quantity)

                    # if calculated_weight:

                    #     tolerance = calculated_weight * 0.03
                    #     print("tolerance---------",tolerance)
                    #     min_weight = calculated_weight - tolerance
                    #     print("min_weight---------",min_weight)
                    #     max_weight = calculated_weight + tolerance
                    #     print("max_weight---------",max_weight)

                    #     if rec.quantity < min_weight or rec.quantity > max_weight:
                    #         raise ValidationError(
                    #             _(
                    #                 "Serial %s weight is outside allowed tolerance.\n"
                    #                 "Expected Weight: %.2f kg\n"
                    #                 "Allowed Range: %.2f - %.2f kg (±3%%)"
                    #             )
                    #             % (
                    #                 rec.serial_number or '',
                    #                 calculated_weight,
                    #                 min_weight,
                    #                 max_weight,
                    #             )
                    #         )

            if mo.product_id.tracking == 'lot' and mo.serial_line_ids:
                mo._create_lots_and_move_lines()
            if mo.scrap_line_ids:
                mo._create_stock_scrap_from_lines()
            # if not mo.product_code:
            #     mo.product_code = mo.action_product_code()

        # return super().button_mark_done()
        res = super().button_mark_done()
        self._create_sale_mo_valuation()

        return res


    def _create_sale_mo_valuation(self):
        for mo in self:
            if not mo.procurement_group_id.sale_id:
                continue
            valuation_layers = self.env['stock.valuation.layer'].search([
                ('stock_move_id.production_id', '=', mo.id)
            ])

            unit_cost = sum(valuation_layers.mapped('unit_cost'))
            total_cost = sum(valuation_layers.mapped('value'))
            existing = self.env['sale.mo.valuation'].search([
                ('sale_id', '=', mo.procurement_group_id.sale_id.id),
                ('reference', '=', mo.name)
            ], limit=1)

            vals = {
                'sale_id': mo.procurement_group_id.sale_id.id,
                'mo_id': mo.id,
                'date': fields.Datetime.now(),
                'reference': mo.name,
                'product_id': mo.product_id.id,
                'quantity': mo.product_qty,
                'unit_cost': unit_cost,
                'total_cost': total_cost,
            }

            if existing:
                existing.write(vals)   
            else:
                self.env['sale.mo.valuation'].create(vals) 
                

    def _create_lots_and_move_lines(self):
        StockLot = self.env['stock.lot']
        StockMoveLine = self.env['stock.move.line']

        move = self.move_finished_ids.filtered(
            lambda m: m.product_id == self.product_id
        )[:1]

        if not move:
            return

        move.move_line_ids.filtered(lambda l: l.state != 'done').unlink()

        for line in self.serial_line_ids:
            if not line.serial_number:
                raise ValidationError("Serial/Lot name is required.")

            lot = StockLot.search([
                ('name', '=', line.serial_number),
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.company_id.id),
            ], limit=1)

            if not lot:
                lot = StockLot.create({
                    'name': line.serial_number,
                    'product_id': self.product_id.id,
                    'company_id': self.company_id.id,
                    'mo_product_code': line.mo_product_code,
                    'product_code': line.po_product_code,
                })

            StockMoveLine.create({
                'move_id': move.id,
                'product_id': self.product_id.id,
                'lot_id': lot.id,
                'quantity': line.quantity,
                'product_uom_id': line.uom_id.id,
                'location_id': move.location_id.id,
                'location_dest_id': line.location_id.id,
                'thickness': line.thickness,
                'thickness_uom': line.thickness_uom,
                'core_id': line.core_id,
                'weight': line.quantity,
                'width_uom': line.width_uom,
                'width': line.width,
                'width_uom': line.width_uom,
                'length': line.length,
                'length_uom': line.length_uom,
                'grade_type': line.grade_type,
                'mo_product_code': line.production_id.product_id.default_code,
            })

    def _create_stock_scrap_from_lines(self):
        StockScrap = self.env['stock.scrap']
        StockLot = self.env['stock.lot']

        for line in self.scrap_line_ids:
            if line.quantity <= 0:
                continue

            lot = StockLot.search([
                ('name', '=', line.serial_number),
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            if not lot and line.serial_number_id:
                lot = line.serial_number_id
            if not lot:
                raise ValidationError(
                    f"Lot/Serial {line.serial_number} not found for scrap."
                )

            scrap = StockScrap.create({
                'product_id': self.product_id.id,
                'scrap_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'lot_id': lot.id,
                # 'location_id': line.source_location_id.id or self.location_src_id.id,
                'location_id': line.location_id.id,
                'scrap_location_id': self.scrap_location_id.id,
                # 'scrap_location_id': line.location_id.id,

                'company_id': self.company_id.id,
                'origin': self.name,
                'production_id': self.id,
                'scrap_reason_tag_ids': [(6, 0, line.scrap_reason_tag_ids.ids)],
            })

            # scrap.action_validate()
            action = scrap.with_context(
                not_unlink_on_discard=True
            ).action_validate()

            if isinstance(action, dict):
                wizard = self.env[action['res_model']].with_context(
                    action.get('context', {})
                ).create({
                    'scrap_id': scrap.id
                })

                wizard.action_done()


    def action_product_code(self):
        month_code = {
            1: 'A', 2: 'B', 3: 'C', 4: 'D',
            5: 'E', 6: 'F', 7: 'G', 8: 'H',
            9: 'I', 10: 'J', 11: 'K', 12: 'L',
        }
        today = date.today()
        year = today.year
        month = month_code[today.month]
        wc = self.workorder_ids[:1].workcenter_id or \
            self.bom_id.operation_ids[:1].workcenter_id

        machine_code = wc.code if wc and wc.code else 'X'
        print("=====machine_code===",machine_code)

        prefix = f"{machine_code}{year}{month}"
        print("====prefix==",prefix)
        last_mo = self.search(
            [('product_code', 'like', prefix + '%')],
            order='product_code desc',
            limit=1
        )

        seq = 1
        if last_mo and last_mo.product_code:
            last_seq = last_mo.product_code[-4:]
            if last_seq.isdigit():
                seq = int(last_seq) + 1

        new_code = f"{prefix}{str(seq).zfill(4)}"
        print("----new_code-----",new_code)
        # self.product_code = new_code

        return f"{prefix}{str(seq).zfill(4)}"






class MrpProductionSerialLine(models.Model):
    _name = 'mrp.production.serial.line'
    _description = 'MRP Production Serial Line'

    production_id = fields.Many2one( 'mrp.production', string='Manufacturing Order',
        ondelete='cascade', required=True
    )
    serial_number = fields.Char(string='Serial Number')
    location_id = fields.Many2one('stock.location', string='Location', domain="[('usage', '=', 'internal')]")
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')

    thickness = fields.Float(string='Thickness')
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron')],default='micron',string=" ")
    width = fields.Float(string='Width')
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch'),('kg', 'Kg'),
                                        ('lbs', 'Lbs'),
                                        ('gm', 'Gm'),],default='mm',string=" ")
    core_id = fields.Selection(selection=[('3','3 Inch'),('6','6 Inch')],string="Core")
    length = fields.Float(string='Length')
    length_uom = fields.Selection(selection=[('m','M'),('feet','Feet')],default='feet',string=" ")
    recived = fields.Float(string='Receive')
    recived_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch'),('kg', 'Kg'),
                                        ('lbs', 'Lbs'),
                                        ('gm', 'Gm'),],default='kg',string=" ")
    billed = fields.Float(string='Billed')
    film_category = fields.Char(string="Film Category",  help="This helps to categorise specific product.")
    film = fields.Char(string="Film", help="Product Film.")
    film_type = fields.Char(string="Film Type", help="Film Type")

    total_input = fields.Float(string=" Input")
    total_output = fields.Float(string=" Output")
    total_scrap = fields.Float(string=" Scrap")

    grade_type = fields.Selection([('a', 'A Grade'),('b', 'B Grade'),],string="Grade")
    mo_product_code = fields.Char(string="MO Product Code")
    po_product_code = fields.Char(string="Product Code")
    density = fields.Float(string="Roll Density")
    treatment_in = fields.Selection([
            ('corona', 'Corona'),
            ('met_corona', 'Met on Corona'),
            ('met_chemical', 'Met on Chemical'),
            ('met_plain', 'Met on Plain'),
            ('plain', 'Plain'),
            ('pvdc', 'PVDC COATED'),
            ('soft_touch', 'SOFT TOUCH'),
            ('alox', 'Top coat Alox'),
        ], string="Treatment IN")

    treatment_out = fields.Selection([
            ('acrylic', 'ACRYLIC'),
            ('corona', 'Corona'),
            ('met_plain', 'Met on Plain'),
            ('met_corona', 'Met on Corona'),
            ('met_corona_out', 'Metallized on Corona Outside'),
            ('met_chemical', 'Metallized on Chemical'),
            ('plain', 'Plain'),
            ('pvdc_out', 'PVDC COATED'),
        ], string="Treatment OUT")



class MrpProductionScrapLine(models.Model):
    _name = 'mrp.production.scrap.line'
    _description = 'MRP Production Scrap Line'

    production_scrap_id = fields.Many2one( 'mrp.production', string='Manufacturing Order',
        ondelete='cascade', required=True
    )
    serial_number_id = fields.Many2one('stock.lot',store=True)
    serial_number = fields.Char(string='Serial Number')
    location_id = fields.Many2one('stock.location', string='Destination Location', domain="[('usage', '=', 'internal')]")
    source_location_id = fields.Many2one('stock.location', string='Source Location')
    quantity = fields.Float(string='Scrap Qty')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    scrap_reason_tag_ids = fields.Many2many( comodel_name='stock.scrap.reason.tag',
        string='Scrap Reason',
    )

    thickness = fields.Float(string='Thickness')
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron')],default='micron',string=" ")
    width = fields.Float(string='Width')
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch'),('kg', 'Kg'),
                                        ('lbs', 'Lbs'),
                                        ('gm', 'Gm'),],default='mm',string=" ")
    core_id = fields.Selection(selection=[('3','3 Inch'),('6','6 Inch')],string="Core")
    length = fields.Float(string='Length')
    length_uom = fields.Selection(selection=[('m','M'),('feet','Feet')],default='feet',string=" ")
    recived = fields.Float(string='Recived')
    billed = fields.Float(string='Billed')
    film_category = fields.Char(string="Film Category",  help="This helps to categorise specific product.")
    film = fields.Char(string="Film", help="Product Film.")
    film_type = fields.Char(string="Film Type", help="Film Type")
    treatment_in = fields.Selection([
            ('corona', 'Corona'),
            ('met_corona', 'Met on Corona'),
            ('met_chemical', 'Met on Chemical'),
            ('met_plain', 'Met on Plain'),
            ('plain', 'Plain'),
            ('pvdc', 'PVDC COATED'),
            ('soft_touch', 'SOFT TOUCH'),
            ('alox', 'Top coat Alox'),
        ], string="Treatment IN")

    treatment_out = fields.Selection([
            ('acrylic', 'ACRYLIC'),
            ('corona', 'Corona'),
            ('met_plain', 'Met on Plain'),
            ('met_corona', 'Met on Corona'),
            ('met_corona_out', 'Metallized on Corona Outside'),
            ('met_chemical', 'Metallized on Chemical'),
            ('plain', 'Plain'),
            ('pvdc_out', 'PVDC COATED'),
        ], string="Treatment OUT")
    


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'
    _description = 'Work Center'


    code = fields.Char('Code', copy=False,required=True)

class MrpConsumables(models.Model):
    _name = 'mrp.consumables'
    _description = 'Consumables Products'

    production_id = fields.Many2one('mrp.production',string='Manufacturing Order',
        ondelete='cascade'
    )
    product_id = fields.Many2one('product.product',string='Consumable Product',required=True,)
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom',string='UoM', related='product_id.uom_id',store=True,readonly=True)

    location_id = fields.Many2one('stock.location',string='Source Location',required=True,
        domain="[('usage', '=', 'internal')]"
    )

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_finish(self):
        res = super().button_finish()

        for wo in self:
            mo = wo.production_id
            if mo and not mo.product_code:
                mo.action_product_code()
        return res


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    _sql_constraints = [
        ('bom_code_unique',
         'unique(code)',
         'BoM Reference must be unique!')
    ]

    cost_price = fields.Float(
        string="Total Cost Price",
        compute="_compute_total_cost",
        store=True,
        digits="Product Price"
    )

    @api.depends('bom_line_ids.product_id','bom_line_ids.product_qty','bom_line_ids.product_id.standard_price',
        'operation_ids.time_cycle_manual','operation_ids.workcenter_id.costs_hour')
    def _compute_total_cost(self):
        for bom in self:
            total = 0.0

            for line in bom.bom_line_ids:
                total += line.product_id.standard_price * line.product_qty

            for operation in bom.operation_ids:
                duration_minutes = operation.time_cycle_manual or 0.0
                cost_per_hour = operation.workcenter_id.costs_hour or 0.0

                total += (duration_minutes / 60.0) * cost_per_hour

            bom.cost_price = total
