from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

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

    thickness_val = fields.Float(string="Thickness", help="This helps to categorise specific product.")
    thickness_uom = fields.Selection(selection=[('guage', 'Guage'), ('micron', 'Micron'), ('mm', 'MM'), ('mil', 'Mil')],
                                     default='micron', string=" ")
    width_val = fields.Float(string="Width", help="This helps to categorise specific product.")
    width_uom = fields.Selection(selection=[('mm', 'MM'), ('inch', 'Inch'), ('mm', 'MM'), ('mil', 'Mil')], default='mm',
                                 string=" ")
    core_id = fields.Selection(selection=[('3', '3 Inch'), ('6', '6 Inch')], string="Core")
    length_val = fields.Float(string="Length", help="Product Length")
    length_uom = fields.Selection(selection=[('m', 'M'), ('feet', 'Feet')], default='feet', string=" ")
    remarks = fields.Text(string="Remarks")