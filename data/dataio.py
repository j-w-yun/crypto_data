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
        """Create directory if it does not exist.
        """
        if not os.path.exists(self._savedir):
            try:
                os.makedirs(self._savedir)
            except FileExistsError:
                pass

    def csv_rename(self, filename, new_filename):
        """Rename a CSV file into a desired filename.

        Args:
            filename (str): Name of file to rename.
            new_filename (str): New name of file.
        """
        new_filepath = '{}\\{}.csv'.format(self._savedir, new_filename)
        if self.csv_check(new_filename, create_file=False):
            os.remove(new_filepath)
        filepath = '{}\\{}.csv'.format(self._savedir, filename)
        os.rename(filepath, new_filepath)

    def csv_newfile(self, filename):
        """Create a new file and write header.

        Args:
            filename (str): Name of file.
        """
        with open('{}\\{}.csv'.format(self._savedir, filename), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            w.writeheader()

    def csv_check(self, filename, create_file=True):
        """Check if file is present. If file is not present, create a new file
        and write header.

        Args:
            filename (str): Name of file.
            create_file (bool): Create file if it does not exist.

        Returns:
            True: If file exists.
            False: If a new file was created.
        """
        try:
            with open('{}\\{}.csv'.format(self._savedir, filename), 'r', newline=''):
                return True
        except FileNotFoundError:
            if create_file:
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

    def csv_get(self, filename):
        """Fetch data stored in file.

        Args:
            filename (str): Name of file.

        Returns:
            A dict of list.
        """
        with open('{}\\{}.csv'.format(self._savedir, filename), 'r', newline='') as f:
            r = csv.DictReader(f)
            fieldnames = r.fieldnames
            data = {fieldname: [] for fieldname in fieldnames}
            for row in r:
                for fieldname in row:
                    data[fieldname].append(row[fieldname])
        return data

    def csv_get_last(self, filename):
        """Fetch the last row in file.

        Args:
            filename (str): Name of file.

        Returns:
            A dict representing the last row stored in file.
        """
        with open('{}\\{}.csv'.format(self._savedir, filename), 'r', newline='') as f:
            r = csv.DictReader(f)
            last_row = None
            for row in r:
                last_row = row
        return last_row
