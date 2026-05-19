
from odoo import models, fields,api
from datetime import date
from odoo.exceptions import ValidationError

class StockLot(models.Model):
    _inherit = 'stock.lot'

    name = fields.Char(string='Serial Numbers', required=True, index=True)
    thickness = fields.Float(string="Thickness",tracking=True)
    weight = fields.Float(string="Weight",tracking=True)
    core_id = fields.Char(string="Core Id",tracking=True)
    core_selection_id = fields.Selection(selection=[('3','3 Inch'),('6','6 Inch')],string="Core")

    qc_status = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], default='pending',tracking=True)

    qc_remark = fields.Text(string="QC Remarks",tracking=True)
    upload_doc = fields.Binary(string="Upload Document",tracking=True)
    failure_reasons = fields.Selection([('physical_damage','Physical Damage'),
                                        ('qlty_fail','Quality / Specification Failure'),
                                       ('manuf_defect','Manufacturing Defects'),
                                        ('others','Others')],
                                       string="Failure Reasons",tracking=True)
    category = fields.Char(string="Film Category",tracking=True,help="This helps to categorise specific product.")
    film = fields.Char(string="Film",tracking=True,help="Product Film.")
    film_type = fields.Char(string="Film Type",tracking=True,help="Film Type")
    lot_number = fields.Char(string="Lot Number",tracking=True,help="Lot Number")
    pallet_no = fields.Char(string="Pallet Number",tracking=True,help="Pallet Number")
    width_val = fields.Float(string="Width",help="This helps to categorise specific product.")
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch')],default='mm',string=" ")
    length_val = fields.Float(string="Length", help="Product Length")
    length_uom = fields.Selection(selection=[('m','M'),('feet','Feet')],default='feet',string=" ")
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron')],default='micron',string=" ")
    weight_uom = fields.Selection(selection=[
                                        ('kg', 'Kg'),
                                        ('lbs', 'Lbs'),
                                        ('gm', 'Gm'),
                                        ],required=True,default='kg',string=" ")

    # product_code =fields.Char(string="Product Code",compute="_compute_product_code",store=True)
    product_code =fields.Char(string="Product Code")
    mo_product_code =fields.Char(string="MO Product Code")
    grade_type = fields.Selection([('a', 'A Grade'),('b', 'B Grade'),],string="Grade")

    production_id = fields.Many2one(
        'mrp.production',
        string="Produced From MO"
    )
    parent_location_id = fields.Many2one(
        'stock.location',
        string='Parent Location',
        compute='_compute_parent_location_id',
        store=True,
    )

    @api.depends('location_id')
    def _compute_parent_location_id(self):
        for rec in self:
            if rec.location_id:
                # FM/Stock/QC HOLD  -> FM/Stock
                rec.parent_location_id = rec.location_id.location_id.id
            else:
                rec.parent_location_id = False
    
    # @api.depends('product_id')
    # def _compute_product_code(self):
    #     for rec in self:
    #         rec.product_code = rec.product_id.default_code if rec.product_id else False

    def action_coa_passed(self):
        self.qc_status = 'passed'

    def action_coa_failed(self):
        for rec in self:
            if not rec.grade_type:
                raise ValidationError("Grade is required when QC status is Failed.")

            rec.qc_status = 'failed'

    def action_reset_to_draft(self):
        self.qc_status = 'pending'

    def action_pass_coa_rolls(self):
        rolls = self.filtered(lambda r: r.qc_status == 'pending')
        if not rolls:
            return True
        res=rolls.write({'qc_status': 'passed'})
        return res

    @api.model
    def _get_next_serial(self, company, product):
        MONTH_MAP = {
            1: 'A', 2: 'B', 3: 'C', 4: 'D',
            5: 'E', 6: 'F', 7: 'G', 8: 'H',
            9: 'I', 10: 'J', 11: 'K', 12: 'L',
        }

        today = date.today()

        year = today.strftime('%y')
        month_code = MONTH_MAP[today.month]
        machine_code = self.env.context.get('machine_code')
        if not machine_code and self.env.context.get('active_model') == 'mrp.production':
            mo = self.env['mrp.production'].browse(self.env.context.get('active_id'))
            if mo and mo.exists():
                wc = mo.workorder_ids[:1].workcenter_id
                if wc:
                    machine_code = wc.code
        else:
            machine_code = self.env.context.get('machine_code', 'X')

        prefix = f"{machine_code}{year}{month_code}"

        last_lot = self.search(
            [
                ('company_id', 'in', [company.id, False]),
                ('name', 'like', prefix + '%'),
            ],
            order="name desc",
            limit=1
        )

        seq = 1
        if last_lot and last_lot.name[-4:].isdigit():
            seq = int(last_lot.name[-4:]) + 1

        return f"{prefix}{str(seq).zfill(4)}"
