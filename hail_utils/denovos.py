import hail as hl

def compute_mendel_denovos(mt, pedigree):
    all_errors, per_fam, per_sample, per_variant = hl.mendel_errors(mt.GT, pedigree)
    mendel_de_novos = all_errors.filter(hl.literal({1,2,5,8}).contains(all_errors.mendel_code))
    return mendel_de_novos
