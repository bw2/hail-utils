import hail as hl

def recompute_AC_AN_AF(mt):
    mt = mt.annotate_rows(info = mt.info.annotate(
        AC = hl.agg.sum(mt.GT.n_alt_alleles()),
        AN = 2 * hl.agg.count_where(hl.is_defined(mt.GT))))
    mt = mt.annotate_rows(info = mt.info.annotate(
        AF = mt.info.AC/mt.info.AN))

    return mt

def annotate_in_LCR(mt, genome_version="GRCh38"):

    if genome_version == "GRCh37":
        lcr_regions = hl.import_locus_intervals("gs://broad-dsp-spec-ops/scratch/weisburd/ref/GRCh37/grch37_LCRs_without_decoys.bed", reference_genome="GRCh37")
    elif genome_version == "GRCh38":
        lcr_regions = hl.import_locus_intervals("gs://broad-dsp-spec-ops/scratch/weisburd/ref/GRCh38/grch38_LCRs_without_decoys.bed", reference_genome="GRCh38")
    else:
        raise ValueError(f"Invalid genome version: {genome_version}")

    return mt.annotate_rows(info = mt.info.annotate(
        in_LCR=hl.is_defined(lcr_regions[mt.locus])))

def annotate_in_segdup(mt, genome_version="GRCh38"):

    if genome_version == "GRCh37":
        segdup_regions = hl.import_locus_intervals("gs://broad-dsp-spec-ops/scratch/weisburd/ref/GRCh37/GRCh37GenomicSuperDup.bed", reference_genome="GRCh37")
    elif genome_version == "GRCh38":
        segdup_regions = hl.import_locus_intervals("gs://broad-dsp-spec-ops/scratch/weisburd/ref/GRCh38/GRCh38GenomicSuperDup.without_decoys.bed", reference_genome="GRCh38")
    else:
        raise ValueError(f"Invalid genome version: {genome_version}")

    return mt.annotate_rows(info = mt.info.annotate(
        in_segdup=hl.is_defined(segdup_regions[mt.locus])))
