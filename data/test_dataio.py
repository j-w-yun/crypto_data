import numpy
from dataio import DataIO

if __name__ == '__main__':

    filename = 'test'
    fieldnames = ['time', 'low', 'high']

    csvio = DataIO('/', fieldnames)
    csvio.csv_newfile(filename)

    test_row1 = {'time': 1.0, 'low': 100, 'high': 101}
    test_row2 = {'time': 2.0, 'low': 101, 'high': 102}
    test_rows = [{'time': 3.0, 'low': 102, 'high': 103},
                 {'time': 4.0, 'low': 103, 'high': 104}]

    exists = csvio.csv_check(filename)
    print(exists)

    print(len(numpy.shape(test_row1)))
    print(len(numpy.shape(test_rows)))

    csvio.csv_append(filename, test_row1)
    csvio.csv_append(filename, test_row2)
    csvio.csv_append(filename, test_rows)

    data = csvio.csv_get(filename, float)
    print(data)
