import hail as hl

def compute_mendel_denovos(mt, pedigree):
    all_errors, per_fam, per_sample, per_variant = hl.mendel_errors(mt.GT, pedigree)
    mendel_de_novos = all_errors.filter(hl.literal({1,2,5,8}).contains(all_errors.mendel_code))
    return mendel_de_novos


def compute_samocha_denovos(mt, pedigree):
    gnomad_ht = hl.read_table("gs://seqr-reference-data/GRCh38/gnomad/gnomad.exomes.r2.1.1.sites.liftover_grch38.ht")
    gnomad_ht = hl.split_multi_hts(gnomad_ht)

    de_novo_priors_ht = gnomad_ht.select(AF=gnomad_ht.freq[gnomad_ht.freq_index_dict["gnomad"]].AF)

    de_novos_ht = hl.de_novo(mt, pedigree, de_novo_priors_ht[mt.row_key].AF)

    de_novos_ht = de_novos_ht.transmute(proband=de_novos_ht.proband.s, father=de_novos_ht.father.s, mother=de_novos_ht.mother.s)

    de_novos_ht = de_novos_ht.annotate(proband_AB=de_novos_ht.proband_entry.AD[1]/(de_novos_ht.proband_entry.AD[0]+de_novos_ht.proband_entry.AD[1]))
    de_novos_ht = de_novos_ht.annotate(proband_DP=de_novos_ht.proband_entry.DP)
    de_novos_ht = de_novos_ht.annotate(proband_GQ=de_novos_ht.proband_entry.GQ)
    de_novos_ht = de_novos_ht.annotate(proband_GT=de_novos_ht.proband_entry.GT)

    de_novos_ht = de_novos_ht.annotate(father_AB=de_novos_ht.father_entry.AD[1]/(de_novos_ht.father_entry.AD[0]+de_novos_ht.father_entry.AD[1]))
    de_novos_ht = de_novos_ht.annotate(father_DP=de_novos_ht.father_entry.DP)
    de_novos_ht = de_novos_ht.annotate(father_GQ=de_novos_ht.father_entry.GQ)
    de_novos_ht = de_novos_ht.annotate(father_GT=de_novos_ht.father_entry.GT)

    de_novos_ht = de_novos_ht.annotate(mother_AB=de_novos_ht.mother_entry.AD[1]/(de_novos_ht.mother_entry.AD[0]+de_novos_ht.mother_entry.AD[1]))
    de_novos_ht = de_novos_ht.annotate(mother_DP=de_novos_ht.mother_entry.DP)
    de_novos_ht = de_novos_ht.annotate(mother_GQ=de_novos_ht.mother_entry.GQ)
    de_novos_ht = de_novos_ht.annotate(mother_GT=de_novos_ht.mother_entry.GT)

    de_novos_ht = de_novos_ht.drop(de_novos_ht.proband_entry, de_novos_ht.father_entry, de_novos_ht.mother_entry)

    return de_novos_ht
