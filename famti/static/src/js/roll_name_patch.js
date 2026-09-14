/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { GenerateDialog } from "@stock/widgets/generate_serial";

patch(GenerateDialog.prototype, {

    setup() {
        super.setup();
        if (this.props.mode === 'generate') {
            this.title = this.props.move.data.has_tracking === 'lot'
                ? _t("Generate Roll Numbers")
                : _t("Generate Roll Numbers");
        } else {
            this.title = this.props.move.data.has_tracking === 'lot'
                ? _t("Import Lots")
                : _t("Import Serials");
        }
    },

});