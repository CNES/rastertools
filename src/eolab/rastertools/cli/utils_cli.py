from eolab.rastertools import RastertoolConfigurationException
import logging
import sys
import click

#TO DO
_logger = logging.getLogger(__name__)

def _extract_files_from_list(cmd_inputs):
    """
    Extracts a list of file paths from a command line input.

    If the input is a single file with a `.lst` extension, it reads the file line-by-line and treats each
    line as an individual file path, returning the list of paths. If the input is already a
    list of file paths, it is returned as-is.

    Args:
        cmd_inputs (list of str):
            Command line inputs for file paths. If it contains a single `.lst` file, this file
            is read to obtain the list of files. Otherwise, it is assumed to be a direct list of files.

    Returns:
        list of str: A list of file paths, either extracted from the `.lst` file or passed directly.

    Example:
        _extract_files_from_list(["files.lst"])

        _extract_files_from_list(["file1.tif", "file2.tif"])

    Notes:
        The `.lst` file is expected to have one file path per line. Blank lines in the `.lst`
        file will be ignored.
    """

    # handle the input file of type "lst"
    if len(cmd_inputs) == 1 and cmd_inputs[0][-4:].lower() == ".lst":
        # parse the listing
        with open(cmd_inputs[0]) as f:
            inputs = f.read().splitlines()
    else:
        inputs = cmd_inputs

    return inputs


def apply_process(ctx, tool, inputs : list):
    """
    Apply the chosen process to a set of input files.

    This function extracts input files, configures the tool, and processes the files
    through the specified tool. It also handles debug settings and intermediate file storage
    (VRT files). In case of any errors, the function logs the exception and terminates the process
    with an appropriate exit code.

    Args:
        ctx (click.Context): The context object containing configuration options like whether
                             to store intermediate VRT files.
        tool (Filtering or Hillshade or ...): The tool instance that has been configured with the provided parameters.
        inputs (str): A path to a list of input files, either as a single `.lst` file or a direct
                      list of file paths.

    Raises:
        RastertoolConfigurationException: If there is a configuration error with the tool.
        Exception: Any other errors that occur during processing.
    """
    try:
        print('@' * 50)
        # handle the input file of type "lst"
        inputs_extracted = _extract_files_from_list(inputs)

        print('@' * 50)
        # setup debug mode in which intermediate VRT files are stored to disk or not
        tool.with_vrt_stored(ctx.obj.get('keep_vrt'))
        print('@' * 50)

        # launch process
        tool.process_files(inputs_extracted)

        _logger.info("Done!")

    except RastertoolConfigurationException as rce:
        print('@'*50)
        _logger.exception(rce)
        sys.exit(2)

    except Exception as err:
        print('!' * 50)
        _logger.exception(err)
        sys.exit(1)
    print('?' * 50)
    sys.exit(0)