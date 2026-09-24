from odoo import models, fields


class ScrapGrade(models.Model):
    _name = "scrap.grade"
    _description = "Scrap Grade"

    name = fields.Char(string="Scrap Grade",required=True)


    active = fields.Boolean(string="Active",default=True)

    _sql_constraints = [
        (
            "unique_scrap_grade_name",
            "unique(name)",
            "Scrap Grade name must be unique."
        )
    ]