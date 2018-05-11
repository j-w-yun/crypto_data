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
        """Create directory if it does not exist."""
        if not os.path.exists(self._savedir):
            try:
                os.makedirs(self._savedir)
            except FileExistsError:
                pass

    def csv_newfile(self, filename):
        """Create a new file and write header.

        Args:
            filename (str): Name of file.
        """
        with open('{}\\{}.csv'.format(self._savedir, filename), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            w.writeheader()

    def csv_check(self, filename):
        """Check if file is present. If file is not present, create a new file
        and write header.

        Args:
            filename (str): Name of file.

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
        """Append a dict or a row of dicts to the last line of file.

        Args:
            filename (str): Name of file.
            data (dict or list of dict): Data to write to file.
        """
        with open('{}\\{}.csv'.format(self._savedir, filename), 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            if len(numpy.shape(data)) > 0:
                for data_row in data:
                    w.writerow(data_row)
            else:
                w.writerow(data)

    def csv_get(self, filename, cast_op=None):
        """Fetch data stored in file.

        Args:
            filename (str): Name of file.
            cast_op (obj, optional): Cast operator.

        Returns:
            A list of dict stored in file.
        """
        data = []
        with open('{}\\{}.csv'.format(self._savedir, filename), 'r', newline='') as f:
            r = csv.DictReader(f)
            for row in r:
                if cast_op:
                    for elem_key in row:
                        row[elem_key] = cast_op(row[elem_key])
                data.append(row)
        return data

    def csv_get_last(self, filename, cast_op=None):
        """Fetch the last row in file.

        Args:
            filename (str): Name of file.
            cast_op (obj, optional): Cast operator.

        Returns:
            A dict representing the last row stored in file.
        """
        data = self.csv_get(filename, cast_op=cast_op)
        if len(data) > 0:
            return data[-1]
        else:
            return None
