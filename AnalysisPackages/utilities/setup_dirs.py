import argparse
from pathlib import Path

from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(file_name):
    psr = PulsarInformationUtility(file_name)
    bands = int(psr.n_bands)
    current_dir = str(Path.cwd())
    for band in range(bands):
        print("saving : "+ current_dir + f"/OutputData/{file_name}/DynamicSpectrum/ch0{str(band)}/")
        Path(current_dir + f"/OutputData/{file_name}/DynamicSpectrum/ch0{str(band)}/") \
            .mkdir(parents=True, exist_ok=True)
        Path(current_dir + f"/OutputData/{file_name}/AveragePulseProfile/ch0{str(band)}/") \
            .mkdir(parents=True, exist_ok=True)
        Path(current_dir + f"/OutputData/{file_name}/TimeSeries/ch0{str(band)}/") \
            .mkdir(parents=True, exist_ok=True)
        # /Users/hrishikesh.s/RRIProject/pulsar-analysis-package/OutputData/B0834+06_20090725_114903/DynamicSpectrum/ch02/ch02_B0834+06_20090725_114903_imagXY.spec


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_name", type=str,
                        help="The mbr filename without the sequence number(eg. B0834+06_20090725_114903)")

    args = parser.parse_args()
    main(args.input_file_name)  # B0834+06_20090725_114903 ch03 XX
