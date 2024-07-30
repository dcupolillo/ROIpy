""" Created on Mon Jun 17 12:05:55 2024
    @author: dcupolillo """


def calculate_line_period(
        rectangle: object,
        dwell_time: float,
        slowest_rate,
        acq_sample_rate=None,
        fill_fraction_spatial: float = 0.9):
    """
    Calculate the line scan period and line acquisition period.

    Parameters:
    - scanfield: ScanField object containing the pixel resolution.
    - pixel_time: Time per pixel.
    - slowest_rate: Slowest scanner sample rate.
    - acq_sample_rate: Acquisition sample rate (optional).
    - fill_fraction_spatial: Spatial fill fraction.

    Returns:
    - line_scan_period: Total period for scanning one line.
    - line_acquisition_period: Active acquisition period for scanning one line.
    """
    pixels_x = rectangle.pixel_resolution_xy[0]
    line_acquisition_period = pixels_x * dwell_time

    if acq_sample_rate is not None:
        scan_acq_samples = np.arange(
            np.ceil(acq_sample_rate * line_acquisition_period / fill_fraction_spatial),
            np.ceil(1.5 * acq_sample_rate * line_acquisition_period / fill_fraction_spatial) + 1
        )
        scan_acq_samples = scan_acq_samples[scan_acq_samples % 2 == 0]
        scan_acq_times = scan_acq_samples / acq_sample_rate
        ctl_samples = scan_acq_times * slowest_rate
        ctl_samples = ctl_samples[ctl_samples == np.round(ctl_samples)]
        if len(ctl_samples) == 0:
            raise ValueError('Invalid sample rates.')
        line_scan_period = min(ctl_samples) / slowest_rate
    else:
        samples_acq = line_acquisition_period * slowest_rate
        samples_turnaround_half = np.ceil(((samples_acq / fill_fraction_spatial) - samples_acq) / 2)
        samples_scan = samples_acq + 2 * samples_turnaround_half
        line_scan_period = samples_scan / slowest_rate

    return line_scan_period, line_acquisition_period


def generate_galvo_path(
        class_var: object,
        rectangle: object,
):
    """
    Generates a scan path for an individual scanfield.
    It computes the path for the Galvo mirrors to cover the
    specified scan area, taking into account the scanning parameters
    and any required transformations.

    Parameters
    ----------
    class_var : object
        DESCRIPTION.

    Returns
    -------
    None.

    """

    line_scan_period = rectangle.

    nx = int(sample_rate * line_scan_period)
    nx_acq = int(sample_rate * line_acquisition_period)
    n_turn = nx - nx_acq
    assert n_turn % 2 == 0, "Turnaround samples must be even."