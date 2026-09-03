from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # film = fields.Char(related="move_id.film",string="Film")
    film = fields.Char(string="Film")
    category = fields.Char(string="Film Category", tracking=True, help="This helps to categorise specific product.")
    # film_type = fields.Char(related="move_id.film_type",string="Film Type", tracking=True, help="Film Type")
    film_type = fields.Char(string="Film Type", tracking=True, help="Film Type")
    lot_number = fields.Char(string="Lot Number", tracking=True, help="Lot Number")
    pallet_no = fields.Char(string="Pallet Number", tracking=True, help="Pallet Number")

    # weight = fields.Float(related="move_id.weight_val",string="Weight (kg)", tracking=True)
    weight = fields.Float(string="Weight (kg)", tracking=True)
    lot_id = fields.Many2one('stock.lot',string='Roll Numbers')
    lot_name = fields.Char(string="Roll Number")

    # weight_uom = fields.Selection(related="move_id.weight_uom",selection=[
    #     ('kg', 'Kg'),
    #     ('lbs', 'Lbs'),
    #     ('gm', 'Gm'),
    # ], required=True, default='kg', string=" ")
    # thickness = fields.Float(related="move_id.thickness_val",string="Thickness (micron)", tracking=True)
    # thickness_uom = fields.Selection(related="move_id.thickness_uom",selection=[('guage', 'Guage'), ('micron', 'Micron')], default='micron', string=" ",
    #                                  tracking=True)
    # width = fields.Float(related="move_id.width_val",string="Width", help="This helps to categorise specific product.")
    # width_uom = fields.Selection(related="move_id.width_uom",selection=[('mm', 'MM'), ('inch', 'Inch')], default='mm', string=" ", tracking=True)
    # core_id = fields.Selection(related="move_id.core_id",selection=[('3', '3 Inch'), ('6', '6 Inch')], string="Core", tracking=True)
    # length = fields.Float(related="move_id.length_val",string="Length", tracking=True, help="Product Length")
    # length_uom = fields.Selection(related="move_id.length_uom",selection=[('m', 'M'), ('feet', 'Feet')], default='feet', string=" ", tracking=True)
    weight_uom = fields.Selection(selection=[
        ('kg', 'Kg'),
        ('lbs', 'Lbs'),
        ('gm', 'Gm'),
    ], required=True, default='kg', string=" ")
    thickness = fields.Float(string="Thickness (micron)", tracking=True)
    thickness_uom = fields.Selection(selection=[('guage', 'Guage'), ('micron', 'Micron')], default='micron', string=" ",
                                        tracking=True)
    width = fields.Float(string="Width", help="This helps to categorise specific product.")
    width_uom = fields.Selection(selection=[('mm', 'MM'), ('inch', 'Inch')], default='mm', string=" ", tracking=True)
    core_id = fields.Selection(selection=[('3', '3 Inch'), ('6', '6 Inch')], string="Core", tracking=True)
    length = fields.Float(string="Length", tracking=True, help="Product Length")
    length_uom = fields.Selection(selection=[('m', 'M'), ('feet', 'Feet')], default='feet', string=" ", tracking=True)
    grade_type = fields.Selection([('a', 'A Grade'),('b', 'B Grade'),],string="Grade")
    mo_product_code =fields.Char(string="MO Product Code")
    # treatment_in = fields.Selection([
    #     ('corona', 'Corona'), ('met_corona', 'Met on Corona'), ('met_chemical', 'Met on Chemical'),
    #     ('met_plain', 'Met on Plain'), ('plain', 'Plain'), ('pvdc', 'PVDC COATED'),
    #     ('soft_touch', 'SOFT TOUCH'), ('alox', 'Top coat Alox'),
    # ], related="move_id.treatment_in", string="Treatment IN")
    # treatment_out = fields.Selection([
    #     ('acrylic', 'ACRYLIC'), ('corona', 'Corona'), ('met_plain', 'Met on Plain'),
    #     ('met_corona', 'Met on Corona'), ('met_corona_out', 'Metallized on Corona Outside'),
    #     ('met_chemical', 'Metallized on Chemical'), ('plain', 'Plain'), ('pvdc_out', 'PVDC COATED'),
    # ], related="move_id.treatment_out", string="Treatment OUT")
    # description = fields.Text(related="move_id.description",string="Film Description")
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
    description = fields.Text(string="Film Description")
    supplier_name = fields.Many2one('res.partner', string="Supplier Name")
    #
    # def _action_done(self):
    #     res = super()._action_done()
    #     for line in self:
    #         if line.lot_id:
    #             previous_code= line.product_id.default_code
    #             line.lot_id.film = line.film
    #             line.lot_id.category = line.category
    #             line.lot_id.film_type = line.film_type
    #             line.lot_id.thickness = line.thickness
    #             line.lot_id.thickness_uom = line.thickness_uom
    #             line.lot_id.weight = line.weight
    #             line.lot_id.width_uom = line.width_uom
    #             line.lot_id.core_id = line.core_id
    #             line.lot_id.lot_number = line.lot_number
    #             line.lot_id.pallet_no = line.pallet_no
    #             line.lot_id.width_val = line.width
    #             line.lot_id.width_uom = line.width_uom
    #             line.lot_id.length_val = line.length
    #             line.lot_id.length_uom = line.length_uom
    #             line.lot_id.grade_type = line.grade_type
    #     return res

    def _action_done(self):
        res = super()._action_done()

        for line in self:
            if not line.lot_id:
                continue
            lot = line.lot_id
            vals = {}
            if line.film:
                vals['film'] = line.film

            if line.category:
                vals['category'] = line.category

            if line.film_type:
                vals['film_type'] = line.film_type

            if line.description:
                vals['film_description'] = line.description

            if line.thickness not in (False, 0):
                vals['thickness'] = line.thickness

            if line.thickness_uom:
                vals['thickness_uom'] = line.thickness_uom

            if line.weight:
                vals['weight'] = line.weight

            if line.weight_uom:
                vals['weight_uom'] = line.weight_uom

            if line.core_id:
                vals['core_id'] = line.core_id

            if line.lot_number:
                vals['lot_number'] = line.lot_number

            if line.pallet_no:
                vals['pallet_no'] = line.pallet_no

            if line.width not in (False, 0):
                vals['width_val'] = line.width

            if line.width_uom:
                vals['width_uom'] = line.width_uom

            if line.length not in (False, 0):
                vals['length_val'] = line.length

            if line.length_uom:
                vals['length_uom'] = line.length_uom

            if line.grade_type:
                vals['grade_type'] = line.grade_type

            if line.treatment_in:
                vals['treatment_in'] = line.treatment_in

            if line.treatment_out:
                vals['treatment_out'] = line.treatment_out

            if line.result_package_id:
                vals['pallet_no'] = line.result_package_id.name

            purchase_line = line.move_id.purchase_line_id

            # if purchase_line and purchase_line.order_id.partner_id:
            #     vals['supplier_name'] = purchase_line.order_id.partner_id.id
            if line.supplier_name:
                vals['supplier_name'] = line.supplier_name.id

            if line.date and not lot.received_date:
                vals['received_date'] = line.date

            if vals:
                lot.write(vals)

        return res

    @api.onchange('lot_name')
    def _onchange_lot_name_check_duplicate(self):
        if self.lot_name:
            existing_lot = self.env['stock.lot'].search([
                ('name', '=', self.lot_name),
            ], limit=1)

            if existing_lot:
                raise ValidationError(
                    _("Serial Number '%s' already exists for the product '%s'. "
                    "Please check the product serial number.")
                    % (self.lot_name, self.product_id.display_name)
                )

class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one(
        'stock.lot',
        string="Lot",
        domain="[('product_id', '=', product_id)]"
    )

    source_mo_id = fields.Many2one(
        'mrp.production',
        string="Source MO",
        compute="_compute_source_mo",
        store=True
    )

    @api.depends('lot_id')
    def _compute_source_mo(self):
        for move in self:
            mo = False
            if move.lot_id:
                move_line = self.env['stock.move.line'].search([
                    ('lot_id', '=', move.lot_id.id),
                    ('move_id.production_id', '!=', False)
                ], limit=1, order="id desc")

                mo = move_line.move_id.production_id if move_line else False

            move.source_mo_id = mo


    # @api.onchange('product_id')
    # def _onchange_product_id_set_lot_domain(self):
    #     if self.product_id:
    #         print("========",self.product_id.lot_ids)
    #         return {
    #             'domain': {
    #                 'lot_id': [
    #                     ('product_id', '=', self.product_id.id),
    #                     ('quantity', '>', 0)
    #                 ]
    #             }
    #         } 

    units_display = fields.Char(
        string="Units",
        compute="_compute_units_display"
    )
    so_type = fields.Selection(
        related='picking_id.sale_id.so_type',
        string="SO Type",
        store=True
    )
    pieces = fields.Float(string="Pieces",compute="_compute_units_display")
    rolls_uom_id = fields.Many2one('uom.uom', string="Units",domain="[('name','=','rolls')]",
        default=lambda self: self.env['uom.uom'].search([('name','=','rolls')], limit=1))
   

    @api.depends('move_line_ids')
    def _compute_units_display(self):
        for rec in self:
            if rec.sale_line_id and rec.sale_line_id.pieces:
                rec.units_display = f"{rec.sale_line_id.pieces} Rolls"
                rec.pieces = rec.sale_line_id.pieces
            else:
                count = len(rec.move_line_ids)
                rec.units_display = "Rolls"
                rec.pieces = count

    weight_val = fields.Float(string="Weight")
    weight_uom = fields.Selection(selection=[
        ('kg', 'Kg'), ('lbs', 'Lbs'), ('gm', 'Gm'),
    ], string=" ")
    thickness_val = fields.Float(string="Thickness")
    thickness_uom = fields.Selection(selection=[
        ('guage', 'Guage'), ('micron', 'Micron'), ('mm', 'MM'), ('mil', 'Mil'),
    ], string=" ")
    width_val = fields.Float(string="Width")
    width_uom = fields.Selection(selection=[
        ('mm', 'MM'), ('inch', 'Inch'), ('mil', 'Mil'),
    ], string=" ")
    core_id = fields.Selection(selection=[('3', '3 Inch'), ('6', '6 Inch')], string="Core")
    category = fields.Char(string="Film Category")
    film = fields.Char(string="Film")
    film_type = fields.Char(string="Film Type")
    length_val = fields.Float(string="Length")
    length_uom = fields.Selection(selection=[('m', 'M'), ('feet', 'Feet')], string=" ")
    pieces = fields.Float(string="Pieces")
    description = fields.Text(string="Film Description")
    remarks = fields.Text(string="Remarks")
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
