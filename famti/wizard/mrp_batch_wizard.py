from odoo import models, fields, api,_
from odoo.exceptions import UserError
from odoo.tools import OrderedSet
from odoo.exceptions import ValidationError

class MrpBatchProduceLine(models.TransientModel):
    _name = 'mrp.batch.produce.line'
    _description = 'Batch Production Line'

    wizard_id = fields.Many2one('mrp.batch.produce', string='Wizard',ondelete='cascade', required=True)
    serial_number = fields.Char(string='Serial Number')
    location_id = fields.Many2one('stock.location', string='Location')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')

    thickness = fields.Float(string='Thickness')
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron')],default='micron',string=" ")
    width = fields.Float(string='Width')
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch')],default='mm',string=" ")
    core_id = fields.Selection(selection=[('3','3 Inch'),('6','6 Inch')],string="Core")
    length = fields.Float(string='Length')
    length_uom = fields.Selection(selection=[('m','M'),('feet','Feet')],default='feet',string=" ")
    recived = fields.Float(string='Recived')
    billed = fields.Float(string='Billed')
    film_category = fields.Char(string="Film Category",  help="This helps to categorise specific product.")
    film = fields.Char(string="Film", help="Product Film.")
    film_type = fields.Char(string="Film Type", help="Film Type")
    scrap = fields.Float(string='Scrap')
    grade_type = fields.Selection([('a', 'A Grade'),('b', 'B Grade'),],string="Grade")
    scrap_reason_tag_ids = fields.Many2many( comodel_name='stock.scrap.reason.tag',
        string='Scrap Reason')
    mo_product_code = fields.Char(string='MO Product Code')
    po_product_code = fields.Char(string='Product Code')
    treatment_in = fields.Selection([
        ('corona', 'Corona'),
        ('met_corona', 'Metalizzed on Corona'),
        ('met_chemical', 'Metallized on Chemical'),
        ('met_plain', 'Metallized on Plain'),
        ('plain', 'Plain'),
        ('pvdc', 'PVDC COATED'),
        ('soft_touch', 'SOFT TOUCH'),
        ('alox', 'Top coat Alox'),
        ('chemical_coat', 'Chemical Coated'),
        ('met_copolymer', 'Met on Copolymer'),
        ('acrylic', 'ACRYLIC'),
        ('copolymer', 'Copolymer'),
        ('special_chemical', 'Special Chemical'),
        ], string="Treatment IN")

    treatment_out = fields.Selection([
        ('acrylic', 'ACRYLIC'),
        ('corona', 'Corona'),
        ('met_plain', 'Metallized on Plain'),
        ('met_corona', 'Metallized on Corona'),
        ('met_chemical', 'Metallized on Chemical'),
        ('plain', 'Plain'),
        ('pvdc_out', 'PVDC COATED'),
        ('soft_touch', 'SOFT TOUCH'),
        ('alox', 'Top coat Alox'),
        ('chemical_coat', 'Chemical Coated'),
        ('met_copolymer', 'Met on Copolymer'),
        ('copolymer', 'Copolymer'),
        ('special_chemical', 'Special Chemical'),
        ], string="Treatment OUT")


    @api.onchange('scrap')
    def _onchange_scrap(self):
        import re
        for rec in self:
            if not rec.scrap or not rec.serial_number:
                continue
            production = rec.wizard_id.production_id
            if not production:
                continue
            component_move = production.move_raw_ids[:1]
            if not component_move:
                continue
            product_name = component_move.product_id.name.replace(" ", "")
            numeric = re.search(r'(\d+)$', rec.serial_number)
            numeric_part = numeric.group(1) if numeric else rec.serial_number
            rec.serial_number = f"W{product_name}"


class MrpBatchProduce(models.TransientModel):
    _inherit = 'mrp.batch.produce'

    sn_quantity = fields.Float(string='Quantity per Lot', store=True,)
    sn_recived_quantity = fields.Float(string='Quantity Received',compute="_compute_total_qty", store=True,)
    line_ids = fields.One2many('mrp.batch.produce.line', 'wizard_id', string='Line Items')
    scrap_reason_tag_ids = fields.Many2many( comodel_name='stock.scrap.reason.tag',
        string='Scrap Reason')

    @api.depends('production_id')
    def _compute_lot_qty(self):
        for wizard in self:
            wizard.lot_qty = 1

    @api.depends('production_id')
    def _compute_total_qty(self):
        for wizard in self:
            wizard.sn_recived_quantity = wizard.production_id.product_qty
            wizard.sn_quantity = wizard.production_id.product_qty

    def action_produce_lots(self):
        self.ensure_one()

        production = self.production_id
        serial_line_vals = []
        scrap_line_vals = []

        if not self.line_ids:
            raise ValidationError("Please add at least one line.")
        
        required_fields = {
            'serial_number': "Serial Number",
            'location_id': "Location",
            'quantity': "Quantity",
            'thickness': "Thickness",
            'thickness_uom': "Thickness UOM",
            'width': "Width",
            'width_uom': "Width UOM",
            'core_id': "Core",
            'length': "Length",
            'length_uom': "Length UOM",
            'grade_type': "Grade Type",
        }

        for index, line in enumerate(self.line_ids, start=1):
            serial = line.serial_number or f"Line {index}"
        
            for field_name, field_label in required_fields.items():
                if not line.scrap or line.scrap == 0:
                    if not line[field_name]:
                        raise ValidationError(f"Line {index}: {field_label} is required.")
                    
        

        for line in self.line_ids:
            
            if line.scrap and line.scrap > 0:
                if not line.scrap_reason_tag_ids:
                    raise ValidationError(
                        f"Serial {serial}: Scrap Reason is required when Scrap is entered."
                    )

            density = 0
            if production.raw_material_move_ids:
                product = production.raw_material_move_ids[0].product_id
                density = product.density or 0

            serial_line_vals.append({
                'production_id': production.id,
                'serial_number': line.serial_number,
                'mo_product_code':line.mo_product_code,
                'po_product_code': line.po_product_code,
                'quantity': line.quantity,
                'uom_id': line.uom_id.id,
                'location_id': line.location_id.id,
                'thickness': line.thickness,
                'thickness_uom': line.thickness_uom,
                'width': line.width,
                'width_uom': line.width_uom,
                'core_id': line.core_id,
                'length': line.length,
                'length_uom': line.length_uom,
                'recived': line.recived,
                'billed': line.billed,
                'total_input': production.qty_producing,
                'total_output': line.quantity,
                'total_scrap': line.scrap,
                'grade_type': line.grade_type,
                'density': density,
                'treatment_in': line.treatment_in,
                'treatment_out': line.treatment_out,
            })

            if line.scrap and line.scrap > 0:
                scrap_line_vals.append({
                    'production_scrap_id': production.id,
                    'source_location_id': production.location_dest_id.id,
                    'scrap_reason_tag_ids': [(6, 0, line.scrap_reason_tag_ids.ids)],
                    'location_id': line.location_id.id, 
                    'serial_number': line.serial_number,
                    'quantity': line.scrap,
                    'uom_id': line.uom_id.id,
                    'thickness': line.thickness,
                    'thickness_uom': line.thickness_uom,
                    'width': line.width,
                    'width_uom': line.width_uom,
                    'core_id': line.core_id,
                    'length': line.length,
                    'length_uom': line.length_uom,
                    'treatment_in': line.treatment_in,
                    'treatment_out': line.treatment_out,
                })
        total_manufactured_qty = sum(self.line_ids.mapped('quantity'))

        if total_manufactured_qty != production.qty_producing:
            raise ValidationError(
                f"The total manufactured quantity ({total_manufactured_qty}) "
                f"must be equal to the Production Quantity ({production.qty_producing})."
            )

        if serial_line_vals:
            self.env['mrp.production.serial.line'].create(serial_line_vals)

        if scrap_line_vals:
            self.env['mrp.production.scrap.line'].create(scrap_line_vals)

        return {'type': 'ir.actions.act_window_close'}


    def action_generate_production_text(self):
        self.ensure_one()
        if not self.lot_name:
            raise UserError(_('Please specify the first serial number you would like to use.'))
        
        lots_name = self.env['stock.lot'].generate_lot_names(self.lot_name, self.lot_qty)
        serial_numbers = [lot['lot_name'] for lot in lots_name]
        self.line_ids = [(5, 0, 0)] 
        qty_per_lot = self.sn_recived_quantity / self.lot_qty
        line_vals = []
        product = self.production_id.product_id
        for serial in serial_numbers:
            line_vals.append((0, 0, {
                'serial_number': serial,
                'mo_product_code':self.production_id.product_id.default_code,
                'po_product_code': self.production_id.move_raw_ids[-1].product_id.default_code,
                'quantity': qty_per_lot,
                'uom_id': self.production_id.product_uom_id.id,
                'location_id': self.production_id.location_dest_id.id,
                'treatment_in': product.treatment_in_selection,
                'treatment_out': product.treatment_out_selection,
                'thickness': product.thickness_val,
                'thickness_uom': product.thickness_uom,
                'width': product.width_val,
                'width_uom': product.width_uom,
            }))
        self.line_ids = line_vals

        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_mrp_batch_produce")
        action['res_id'] = self.id
        return action


    def _production_text_to_object(self, mark_done=False):
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("Please generate serial/lot lines first."))

        productions_amount = []
        productions_lot_names = []

        for line in self.line_ids:
            if not line.serial_number:
                raise UserError(_("Serial/Lot number is missing in a line."))
            if line.quantity <= 0:
                raise UserError(_("Quantity must be greater than zero."))

            productions_lot_names.append(line.serial_number)
            productions_amount.append(line.quantity)

        productions = self.production_id._split_productions({
            self.production_id: productions_amount
        })

        lots = self.env['stock.lot'].search([
            ('company_id', 'in', [self.production_id.company_id.id, False]),
            ('name', 'in', productions_lot_names),
            ('product_id', '=', self.production_id.product_id.id),
        ])

        existing_lot_names = lots.mapped('name')
        new_lots = []

        for lot_name in productions_lot_names:
            if lot_name not in existing_lot_names:
                new_lots.append({
                    'name': lot_name,
                    'product_id': self.production_id.product_id.id,
                    'company_id': self.production_id.company_id.id,
                })

        if new_lots:
            lots |= self.env['stock.lot'].create(new_lots)

        lots_by_name = {lot.name: lot for lot in lots}

        productions_to_set = OrderedSet()
        for production, line in zip(productions, self.line_ids):
            production.lot_producing_id = lots_by_name[line.serial_number]
            production.qty_producing = line.quantity
            production.set_qty_producing()
            productions_to_set.add(production.id)

        productions = self.env['mrp.production'].browse(productions_to_set)

        if mark_done:
            return productions.with_context(from_wizard=True).button_mark_done()

        print_actions = productions._autoprint_mass_generated_lots()
        if print_actions:
            return {
                'type': 'ir.actions.client',
                'tag': 'do_multi_print',
                'params': {'reports': print_actions},
            }
