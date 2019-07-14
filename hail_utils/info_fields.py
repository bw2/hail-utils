import hail as hl

def recompute_AC_AN_AF(mt):
    mt = mt.annotate_rows(info = mt.info.annotate(
        AC = hl.agg.sum(mt.GT.n_alt_alleles()),
        AN = 2 * hl.agg.count_where(hl.is_defined(mt.GT))))
    mt = mt.annotate_rows(info = mt.info.annotate(
        AF = mt.info.AC/mt.info.AN))

    return mt


