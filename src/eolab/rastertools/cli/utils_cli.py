from eolab.rastertools import RastertoolConfigurationException
import logging
import sys
import click

_logger = logging.getLogger(__name__)

all_opt = click.option('-a', '--all','all_bands', type=bool, is_flag=True, help="Process all bands")

band_opt = click.option('-b','--bands', type=int, multiple = True, help="List of bands to process")

win_opt = click.option('-ws', '--window_size', type=int, default = 1024, help="Size of tiles to distribute processing, default: 1024")

pad_opt = click.option('-p', '--pad',default="edge", type=click.Choice(['none','edge','maximum','mean','median','minimum','reflect','symmetric','wrap']),
              help="Pad to use around the image, default : edge" 
                  "(see https://numpy.org/doc/stable/reference/generated/numpy.pad.html"
                  " for more information)")

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

    This function extracts input files from a provided list or direct paths, configures the specified tool,
    and processes the files through the given tool. Additionally, it handles debug settings (such as storing
    intermediate VRT files) and manages any exceptions during the process. If an error occurs, the function
    logs the exception and terminates the process with an appropriate exit code.

    Args:
        ctx (click.Context):
            The context object that contains configuration options.

        tool (Filtering or Hillshade or any raster processing tool):
            The configured tool instance that will apply the process to the input files. The tool should have
            been properly set up with parameters.

        inputs (list or str):
            A list of input file paths or a path to a `.lst` file containing a list of input file paths.
            This argument specifies the files that the tool will process.

    Raises:
        RastertoolConfigurationException:
            If there is a configuration error with the tool or its parameters.

        Exception:
            Any other exceptions that occur during the processing of the input files.
    """
    try:
        # handle the input file of type "lst"
        inputs_extracted = _extract_files_from_list(inputs)

        # setup debug mode in which intermediate VRT files are stored to disk or not
        tool.with_vrt_stored(ctx.obj.get('keep_vrt'))

        # launch process
        tool.process_files(inputs_extracted)

        _logger.info("Done!")

    except RastertoolConfigurationException as rce:
        _logger.exception(rce)
        sys.exit(2)

    except Exception as err:
        _logger.exception(err)
        sys.exit(1)

    sys.exit(0)