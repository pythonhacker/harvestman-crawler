var v_fixDblKey = 0;
function fixDblKey() {
        if (v_fixDblKey != 0) {
                return true;
        } else {
                v_fixDblKey = setTimeout('v_fixDblKey = 0;', 10);
                return false;
        }
}
