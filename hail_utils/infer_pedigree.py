####################################################
### Kristen Laricchia's pedigree inference code  ###
####################################################

from collections import defaultdict
import hail as hl
import logging

from typing import Dict, Tuple, Set, List, Union

from hail_utils.filters import filter_to_biallelics, filter_to_autosomes, ld_prune


def compute_kinship_ht(mt, genome_version="GRCh38"):

    mt = filter_to_biallelics(mt)
    mt = filter_to_autosomes(mt)
    mt = mt.filter_rows(
        hl.is_snp(mt.alleles[0], mt.alleles[1]))

    mt = hl.variant_qc(mt)
    mt = mt.filter_rows(mt.variant_qc.call_rate > 0.99)
    mt = mt.filter_rows(mt.info.AF > 0.001) # leaves 100% of variants

    mt = ld_prune(mt, genome_version=genome_version)

    ibd_results_ht = hl.identity_by_descent(mt, maf=mt.info.AF, min=0.10, max=1.0)
    ibd_results_ht = ibd_results_ht.annotate(
        ibd0 = ibd_results_ht.ibd.Z0,
        ibd1 = ibd_results_ht.ibd.Z1,
        ibd2 = ibd_results_ht.ibd.Z2,
        pi_hat = ibd_results_ht.ibd.PI_HAT
    ).drop("ibs0","ibs1","ibs2","ibd")


    kin_ht = ibd_results_ht

    # filter to anything above the relationship of a grandparent
    first_degree_pi_hat = .40
    grandparent_pi_hat = .20
    grandparent_ibd1 = 0.25
    grandparent_ibd2 = 0.15

    kin_ht = kin_ht.key_by("i","j")
    kin_ht = kin_ht.filter(
        (kin_ht.pi_hat > first_degree_pi_hat) |
        ((kin_ht.pi_hat > grandparent_pi_hat) & (kin_ht.ibd1 > grandparent_ibd1) & (kin_ht.ibd2 < grandparent_ibd2)))

    kin_ht = kin_ht.annotate(relation = hl.sorted([kin_ht.i, kin_ht.j])) #better variable name

    return kin_ht




def infer_families(kin_ht: hl.Table,   # the kinship hail table
                   sex: Dict[str, bool], # the dictionary of sexes
                   i_col: str = 'i', # the rest of these are default that can be set to something else if needed
                   j_col: str = 'j',
                   pi_hat_col: str = 'pi_hat',
                   ibd2_col: str = 'ibd2',
                   ibd1_col: str = 'ibd1',
                   ibd0_col: str = 'ibd0',
                   first_degree_threshold: Tuple[float, float] = (0.4, 0.75),
                   second_degree_threshold: Tuple[float, float] = (0.195, 0.3),
                   ibd1_second_degree_threshold: float = 0.40,
                   ibd2_parent_offspring_threshold: float = 0.30,
                   ibd1_parent_offspring_threshold: float = 0.70,
                   ibd0_parent_offspring_threshold: float = 0.15

                   ) -> hl.Pedigree:
    """
    Infers familial relationships from the results of pc_relate and sex information.
    Note that both kinship and ibd2 are needed in the pc_relate output.
    This function returns a pedigree containing trios inferred from the data. Family ID can be the same for multiple
    trios if one or more members of the trios are related (e.g. sibs, multi-generational family). Trios are ordered by family ID.
    Note that this function only returns complete trios defined as:
    one child, one father and one mother (sex is required for both parents)
    :param Table kin_ht: pc_relate output table
    :param dict of str -> bool sex: A dict containing the sex for each sample. True = female, False = male, None = unknown
    :param str i_col: Column containing the 1st sample id in the ibd table
    :param str j_col: Column containing the 2nd sample id in the ibd table
    #:param str kin_col: Column containing the kinship in the ibd table
    :param str pi_hat_col: Column containing the pi_hat in the ibd table
    :param str ibd2_col: Column containing ibd2 in the pc_relate table
    :param (float, float) first_degree_threshold: Lower/upper bounds for kin for 1st degree relatives
    :param (float, float) second_degree_threshold: Lower/upper bounds for kin for 2nd degree relatives
    :param float ibd2_parent_offspring_threshold: Upper bound on ibd2 for a parent/offspring
    :return: Pedigree containing all trios in the data
    :rtype: Pedigree
    """

    def get_fam_samples(sample: str,
                        fam: Set[str],
                        samples_rel: Dict[str, Set[str]],
                        ) -> Set[str]:
        """
        Given a sample, its known family and a dict that links samples with their relatives, outputs the set of
        samples that constitute this sample family.
        :param str sample: sample
        :param dict of str -> set of str samples_rel: dict(
        :param set of str fam: sample known family
        :return: Family including the sample
        :rtype: set of str
        """
        fam.add(sample) # usually this starts out as a blank set except for the case two lines below
        for s2 in samples_rel[sample]: # iterate through the sample's relatives
            if s2 not in fam:
                fam = get_fam_samples(s2, fam, samples_rel) # this part is to get who s2 is related to but that sample may not have been related to?
        return fam

    def get_indexed_ibd(
            pc_relate_rows: List[hl.Struct]
    ) -> Dict[Tuple[str, str], float]:
        """
        Given rows from a pc_relate table, creates dicts with:
        keys: Pairs of individuals, lexically ordered
        values: ibd2, ibd1, ibd0
        :param list of hl.Struct pc_relate_rows: Rows from a pc_relate table
        :return: Dict of lexically ordered pairs of individuals -> kinship
        :rtype: dict of (str, str) -> float
        """
        ibd2 = dict()
        ibd1 = dict()
        ibd0 = dict()
        for row in pc_relate_rows:
            ibd2[tuple(sorted((row[i_col], row[j_col])))] = row[ibd2_col] # this is just getting the ibd2 value for every sample pair
            ibd1[tuple(sorted((row[i_col], row[j_col])))] = row[ibd1_col] # this is just getting the ibd1 value for every sample pair
            ibd0[tuple(sorted((row[i_col], row[j_col])))] = row[ibd0_col] # this is just getting the ibd0 value for every sample pair

        return ibd2,ibd1,ibd0



    def get_parents(
            possible_parents: List[str],
            relative_pairs: List[Tuple[str, str]],
            sex: Dict[str, bool]
    ) -> Union[Tuple[str, str], None]:
        """
        Given a list of possible parents for a sample (first degree relatives with low ibd2),
        looks for a single pair of samples that are unrelated with different sexes.
        If a single pair is found, return the pair (father, mother)
        :param list of str possible_parents: Possible parents
        :param list of (str, str) relative_pairs: Pairs of relatives, used to check that parents aren't related with each other
        :param dict of str -> bool sex: Dict mapping samples to their sex (True = female, False = male, None or missing = unknown)
        :return: (father, mother) if found, `None` otherwise
        :rtype: (str, str) or None
        """


        parents = []
        logging.info(f"You have {len(possible_parents)} possible parent(s)")
        while len(possible_parents) > 1: # go through the entire list of possible parents
            p1 = possible_parents.pop() # start with the first possible parent

            for p2 in possible_parents:
                logging.info(str(tuple(sorted((p1,p2)))) + '\n')

                if tuple(sorted((p1,p2))) not in relative_pairs: # to what degree is a "relative"? will this work for grandparent, mom, child?
                    logging.info("your potential parent's don't appear to be relatives\n")
                    logging.info("SEX p1: " + str(sex.get(p1)) + '\n')
                    logging.info("SEX p2: " + str(sex.get(p2))+'\n')

                    if sex.get(p1) is False and sex.get(p2):
                        parents.append((p1,p2))
                        logging.info("found in order 1\n")
                    elif sex.get(p1) and sex.get(p2) is False:
                        parents.append((p2,p1))
                        logging.info("found in order 2\n")
                else:
                    logging.info("Your Parents are Related!!!\n\n")

        if len(parents) == 1:
            logging.info("Found your parents!\n")
            return parents[0]

        return None

    # Duplicated samples to remove (If not provided, this function won't work as it assumes that each child has exactly two parents)
    duplicated_samples = set()
    try:
        dups = hl.literal(duplicated_samples)
    except:
        dups = hl.empty_array(hl.tstr)


    first_degree_pairs = kin_ht.filter(
        (kin_ht[pi_hat_col] >= first_degree_threshold[0]) &
        (kin_ht[pi_hat_col] <= first_degree_threshold[1]) &
        ~dups.contains(kin_ht[i_col]) &
        ~dups.contains(kin_ht[j_col]) # so not including any duplicate samples
    ).collect()

    first_degree_relatives = defaultdict(set)
    for row in first_degree_pairs:
        first_degree_relatives[row[i_col]].add(row[j_col]) # so you're making a list for every sample that includes any other sample they are related to by first degree
        first_degree_relatives[row[j_col]].add(row[i_col])


    # Add second degree relatives for those samples
    # This is needed to distinguish grandparent - child - parent from child - mother, father down the line
    first_degree_samples = hl.literal(set(first_degree_relatives.keys()))

    second_degree_samples = kin_ht.filter(
        ((kin_ht[pi_hat_col] >= first_degree_threshold[0]) &
         (kin_ht[pi_hat_col] <= first_degree_threshold[1])) |

        ((kin_ht[pi_hat_col] >= second_degree_threshold[0]) &
         (kin_ht[ibd1_col] >= ibd1_second_degree_threshold) &
         (kin_ht[pi_hat_col] < second_degree_threshold[1]))
    ).collect()


    ibd2,ibd1,ibd0 = get_indexed_ibd(second_degree_samples) # this is just getting the ibd values for every sample pair

    fam_id = 1
    trios = []
    duos = []
    decisions = {}
    while len(first_degree_relatives) > 0:
        s_fam = get_fam_samples(list(first_degree_relatives)[0], set(),
                                first_degree_relatives) # just feed in the entire dictionary because it gets keyed out to only that sample in the function anyway
        for s in s_fam:
            logging.info(f"Processing sample: {s}")
            s_rel = first_degree_relatives.pop(s) # because your popping, the above index of [0] will appropriately be updated
            possible_parents = []
            for rel in s_rel: # so s rel is a list of all the people s (which was popped off) was related to by first degree

                if (ibd2[tuple(sorted((s, rel)))] <= ibd2_parent_offspring_threshold) & \
                    (ibd1[tuple(sorted((s, rel)))] >= ibd1_parent_offspring_threshold) &  \
                    (ibd0[tuple(sorted((s, rel)))] <= ibd0_parent_offspring_threshold): # if the ib2 value for that pair is below that parent threshold
                    possible_parents.append(rel)

            #these will be the proband-offspring only pairs
            if len(possible_parents) == 1:
                duos.append(sorted((s, possible_parents[0])))
                decisions[s] = possible_parents[0]
            else:
                parents = get_parents(possible_parents, list(ibd2.keys()), sex)

                decisions[s] = parents

                if parents is not None: # just formatting the trio output here
                    trios.append(hl.Trio(s=s, fam_id=str(fam_id), pat_id=parents[0], mat_id=parents[1], is_female=sex.get(s)))

        fam_id += 1

    return hl.Pedigree(trios), duos, decisions



def get_duplicated_samples_ibd(
        kin_ht: hl.Table,
        i_col: str = 'i',
        j_col: str = 'j',
        pi_hat_col: str = 'pi_hat',
        duplicate_threshold: float = 0.90
) -> List[Set[str]]:
    """
    Given a ibd output Table, extract the list of duplicate samples. Returns a list of set of samples that are duplicates.
    :param Table kin_ht: ibd output table
    :param str i_col: Column containing the 1st sample
    :param str j_col: Column containing the 2nd sample
    :param str pi_hat_col: Column containing the pi_hat value
    :param float duplicate_threshold: pi_hat threshold to consider two samples duplicated
    :return: List of samples that are duplicates
    :rtype: list of set of str
    """

    def get_all_dups(s, dups, samples_duplicates): # should add docstring (sample, empty set, duplicates)
        if s in samples_duplicates:
            dups.add(s)
            s_dups = samples_duplicates.pop(s) # gives u the value with that key
            for s_dup in s_dups:
                if s_dup not in dups:
                    dups = get_all_dups(s_dup, dups, samples_duplicates)
        return dups

    dup_rows = kin_ht.filter(kin_ht[pi_hat_col] > duplicate_threshold).collect()

    samples_duplicates = defaultdict(set) #key is sample, value is set of that sample's duplicates
    for row in dup_rows:
        samples_duplicates[row[i_col]].add(row[j_col])
        samples_duplicates[row[j_col]].add(row[i_col])

    duplicated_samples = []
    while len(samples_duplicates) > 0:
        duplicated_samples.append(get_all_dups(list(samples_duplicates)[0], set(), samples_duplicates))

    return duplicated_samples


def impute_sex(mt):
    vcf_samples = mt.s.collect()
    imputed_sex = hl.impute_sex(mt.GT).collect()

    for sample, imputed_sex_struct in zip(vcf_samples, imputed_sex):
        print(f"{sample}   {'F' if imputed_sex_struct.is_female else 'M'}  {imputed_sex_struct.f_stat:0.3f}   {imputed_sex_struct.observed_homs/imputed_sex_struct.expected_homs:0.2f}")

    is_female_dict = {sample: imputed_sex_struct.is_female for sample, imputed_sex_struct in zip(vcf_samples, imputed_sex)}
    return is_female_dict
