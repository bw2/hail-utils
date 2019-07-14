import hail as hl
from hail_utils.io import file_exists


def get_gnomad_ld_pruned_mt(genome_version="GRCh38"):

    gnomad_ld_pruned_hg37_path = "gs://gnomad/sample_qc/mt/gnomad.joint.high_callrate_common_biallelic_snps.pruned.mt"
    gnomad_ld_pruned_hg38_path = "gs://seqr-bw2/ref/GRCh38/gnomad_ld_pruned.mt"

    if genome_version == "GRCh37":
        return hl.read_matrix_table(gnomad_ld_pruned_hg37_path)
    elif genome_version == "GRCh38":
        if not file_exists(gnomad_ld_pruned_hg38_path):

            grch37 = hl.get_reference('GRCh37')
            grch37.add_liftover("gs://hail-common/references/grch37_to_grch38.over.chain.gz", 'GRCh38') # doesn't like when try to add on chain file more than once

            gnomad_ld_pruned_mt = hl.read_matrix_table(gnomad_ld_pruned_hg37_path)
            gnomad_ld_pruned_mt = gnomad_ld_pruned_mt.annotate_rows(liftover_locus = hl.liftover(gnomad_ld_pruned_mt.locus, 'GRCh38'))
            gnomad_ld_pruned_mt = gnomad_ld_pruned_mt.filter_rows(hl.is_defined(gnomad_ld_pruned_mt.liftover_locus))
            gnomad_ld_pruned_mt = gnomad_ld_pruned_mt.rename({'locus': 'locus_grch37'}).rename({'liftover_locus': 'locus'})
            gnomad_ld_pruned_mt = gnomad_ld_pruned_mt.key_rows_by('locus','alleles')
            gnomad_ld_pruned_mt.write(gnomad_ld_pruned_hg38_path)

        return hl.read_matrix_table(gnomad_ld_pruned_hg38_path)
    else:
        raise ValueError(f"Invalid genome version: {genome_version}")


def ld_prune(mt, genome_version="GRCh38"):
    gnomad_ld_pruned_mt = get_gnomad_ld_pruned_mt(genome_version)

    return mt.filter_rows(hl.is_defined(gnomad_ld_pruned_mt.index_rows(mt.row_key)))



def filter_out_LCRs(mt, genome_version="GRCh38"):

    if genome_version == "GRCh38":
        lcr_regions = hl.import_locus_intervals("gs://broad-dsp-spec-ops/scratch/weisburd/ref/GRCh38/grch38_LCRs_without_decoys.bed", reference_genome="GRCh38")
    else:
        raise ValueError(f"Invalid genome version: {genome_version}")

    return mt.filter_rows(hl.is_missing(lcr_regions[mt.locus]))

def filter_out_segdups(mt, genome_version="GRCh38"):

    if genome_version == "GRCh38":
        segdup_regions = hl.import_locus_intervals("gs://broad-dsp-spec-ops/scratch/weisburd/ref/GRCh38/GRCh38GenomicSuperDup.without_decoys.bed", reference_genome="GRCh38")
    else:
        raise ValueError(f"Invalid genome version: {genome_version}")

    return mt.filter_rows(hl.is_missing(segdup_regions[mt.locus]))


def filter_out_variants_where_all_samples_are_hom_ref(mt):

    return mt.filter_rows(hl.agg.count_where(mt.GT.is_non_ref()) > 0, keep=True)
