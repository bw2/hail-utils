import hail as hl


def subset(mt, sample_ids):
    mt = mt.filter_cols(sample_ids.contains(mt.s))
    mt = mt.filter_rows(hl.agg.any(mt.GT.is_non_ref()))

    return mt