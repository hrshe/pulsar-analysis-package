import unittest

from AnalysisPackages.synchronization import synchronization_single


class TestSynchronization(unittest.TestCase):
    def test_int2str(self):
        self.assertEqual('010', synchronization_single.int2str(10, 3), "there should be three digits")
        self.assertEqual('001', synchronization_single.int2str(1, 3), "there should be three digits")
        self.assertEqual('099', synchronization_single.int2str(99, 3), "there should be three digits")
        self.assertEqual('0888', synchronization_single.int2str(888, 4), "there should be four digits")

    def test_double_arr_to_list(self):
        self.assertEqual([1, 2, 3, 4], synchronization_single.double_arr_to_list([[1, 2], [3, 4]]))
        self.assertEqual([1, 2, 3, 4], synchronization_single.double_arr_to_list([[1], [2, 3, 4]]))


if __name__ == "__main__":
    unittest.main()
