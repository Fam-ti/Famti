from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MrpProductionScrapWizard(models.TransientModel):
    _name = 'mrp.production.scrap.wizard'
    _description = 'MO Scrap Wizard'

    production_id = fields.Many2one('mrp.production', required=True)

    product_id = fields.Many2one('product.product')
    scrap_reason_tag_ids = fields.Many2many( comodel_name='stock.scrap.reason.tag',
        string='Scrap Reason',required=True
    )
    location_id = fields.Many2one('stock.location', string='Source Location')
    scrap_location_id = fields.Many2one('stock.location',
        domain=[('scrap_location', '=', True)]
    )
    date = fields.Datetime(default=fields.Datetime.now)
    company_id = fields.Many2one('res.company')

    line_ids = fields.One2many('mrp.production.scrap.wizard.line','wizard_id',
        string="Scrap Lines"
    )


    def action_confirm_scrap(self):
        scrap_lines_vals = []

        for line in self.line_ids:
            if line.scrap_qty <= 0:
                continue
            if line.scrap_qty > line.available_qty:
                raise ValidationError(
                    _("Scrap quantity cannot exceed available quantity for serial %s")
                    % (line.serial_line_id.serial_number)
                )
            print("no",line.serial_number_id)
            scrap_lines_vals.append({
                'production_scrap_id': self.production_id.id,
                'source_location_id': self.location_id.id,
                'location_id': self.scrap_location_id.id,
                'serial_number_id':line.serial_number_id.id,
                'serial_number': line.serial_number,
                'quantity': line.scrap_qty,
                'uom_id': line.uom_id.id,
                'scrap_reason_tag_ids': [(6, 0, self.scrap_reason_tag_ids.ids)],
                'thickness': line.thickness,
                'thickness_uom': line.thickness_uom,
                'width': line.width,
                'width_uom': line.width_uom,
                'core_id': line.core_id,
                'length': line.length,
                'length_uom': line.length_uom,
                'recived': line.recived,
                'billed': line.billed,
                'film_category': line.film_category,
                'film': line.film,
                'film_type': line.film_type,
            })


        if scrap_lines_vals:
            self.env['mrp.production.scrap.line'].create(scrap_lines_vals)

        return {'type': 'ir.actions.act_window_close'}


class MrpProductionScrapWizardLine(models.TransientModel):
    _name = 'mrp.production.scrap.wizard.line'
    _description = 'MO Scrap Wizard Line'

    wizard_id = fields.Many2one(
        'mrp.production.scrap.wizard',
        required=True,
        ondelete='cascade'
    )

    serial_line_id = fields.Many2one(
        'mrp.production.serial.line',
        string="Serial Line"
    )
    serial_number_id = fields.Many2one('stock.lot',store=True)
    serial_number = fields.Char(readonly=True,store=True)
    available_qty = fields.Float(readonly=True,store=True)
    scrap_qty = fields.Float(string="Scrap Qty")
    uom_id = fields.Many2one('uom.uom', readonly=True,store=True)
    location_id = fields.Many2one('stock.location', readonly=True,store=True)

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
