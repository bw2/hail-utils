
import hail as hl
import os


def file_exists(fname: str) -> bool:
    """
    Check whether a file exists.
    Supports either local or Google cloud (gs://) paths.
    If the file is a Hail file (.ht, .mt extensions), it checks that _SUCCESS is present.
    :param str fname: File name
    :return: Whether the file exists
    :rtype: bool
    """
    _, fext = os.path.splitext(fname)
    if fext in ['.ht', '.mt']:
        fname = os.path.join(fname, '_SUCCESS')

    if fname.startswith('gs://'):
        return hl.hadoop_exists(fname)
    else:
        return os.path.isfile(fname)
