import unittest
from pathlib import Path

from AnalysisPackages.utilities import pulsar_information_utility

root_dirname = str(Path(__file__).parent.parent.absolute())
config_filename = root_dirname + '/AnalysisPackages/resources/config.txt'


class TestPulsarInformationUtility(unittest.TestCase):
    # def setUp(self):
    #     pulsar_information_utility.config = False

    def test_get_intermediate_frequency(self):
        self.assertEqual(70, pulsar_information_utility.get_intermediate_frequency(1))
        self.assertEqual(70, pulsar_information_utility.get_intermediate_frequency(2))
        self.assertEqual(140, pulsar_information_utility.get_intermediate_frequency(3))
        self.assertEqual(140, pulsar_information_utility.get_intermediate_frequency(4))
        self.assertEqual(140, pulsar_information_utility.get_intermediate_frequency(5))
        self.assertEqual(140, pulsar_information_utility.get_intermediate_frequency(6))
        self.assertEqual(140, pulsar_information_utility.get_intermediate_frequency(7))
        self.assertEqual(140, pulsar_information_utility.get_intermediate_frequency(8))
        self.assertEqual(140, pulsar_information_utility.get_intermediate_frequency(9))
        with self.assertRaises(ValueError):
            pulsar_information_utility.get_intermediate_frequency(12)

    def test_config_set_central_frequency(self):
        config = pulsar_information_utility.config_set_central_frequency(2, 20.0)
        self.assertEqual('20.0', config.get('channel-2-specific', 'central_frequency'))

    def test_read_config(self):
        config = pulsar_information_utility.read_config(config_filename)
        self.assertIsNotNone(config.sections())
        self.assertNotEqual(0, len(config.sections()))  # if this fails, check if config.txt is not empty

    def test_time_delay_2_packet_delay(self):
        self.assertEqual(1000, pulsar_information_utility.time_delay_2_packet_delay(512 / 33000, 33000),
                         "1000 packets with 512 samples in a packet sampled at 33MHz " +
                         "should span across (1000*512/(33*10^3)) milli seconds")

    def test_config_set_sync_dispersion_delay_packet_frequency(self):
        config = pulsar_information_utility.config_set_sync_dispersion_delay_packet_frequency(2, 1000)
        self.assertEqual('1000', config.get('channel-2-specific', 'sync_dispersion_delay_packet'))


if __name__ == "__main__":
    unittest.main()
