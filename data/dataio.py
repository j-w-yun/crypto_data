import csv
import os
import numpy


class DataIO:

    def __init__(self, savedir, fieldnames):
        self._savedir = savedir
        self._fieldnames = fieldnames
        self._make_savedir()

    @property
    def fieldnames(self):
        return self._fieldnames

    def _make_savedir(self):
        if not os.path.exists(self._savedir):
            try:
                os.makedirs(self._savedir)
            except FileExistsError:
                pass

    def csv_newfile(self, filename):
        with open('{}\\{}.csv'.format(self._savedir, filename), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            w.writeheader()

    def csv_check(self, filename):
        """Checks if file is present. If not, creates a new file and writes
        header.

        Args:
            filename(str): Name of file.

        Returns:
            True: If file exists.
            False: If a new file was created.
        """
        try:
            with open('{}\\{}.csv'.format(self._savedir, filename), 'r', newline=''):
                return True
        except FileNotFoundError:
            self.csv_newfile(filename)
        return False

    def csv_append(self, filename, data):
        with open('{}\\{}.csv'.format(self._savedir, filename), 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            if len(numpy.shape(data)) > 0:
                for data_row in data:
                    w.writerow(data_row)
            else:
                w.writerow(data)

    def csv_get(self, filename, fmt_str=None):
        data = []
        with open('{}\\{}.csv'.format(self._savedir, filename), 'r', newline='') as f:
            r = csv.DictReader(f)
            for row in r:
                if fmt_str:
                    for elem_key in row:
                        row[elem_key] = fmt_str(row[elem_key])
                data.append(row)
        return data

    def csv_get_last(self, filename, fmt_str=None):
        return self.csv_get(filename, fmt_str=fmt_str)[-1]
