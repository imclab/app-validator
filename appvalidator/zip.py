from zipfile import ZipFile
import zlib


def to_utf8(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return s


class ZipPackage(object):
    """
    A ZIP reader and management class. Allows fun things like reading, listing,
    and extracting files from a ZIP file without you needing to worry about
    things like zip files or IO.
    """

    def __init__(self, package, mode="r", name=None):
        self.zf = ZipFile(package, mode=mode)

        # Store away the filename for future use.
        self.filename = name or package
        self.extension = self.filename.split(".")[-1]

        self.contents_cache = None
        self.broken_files = set()

        self.file_cache = {}

    def __iter__(self):
        return (name for name in self.zf.namelist() if
                name not in self.broken_files)

    def __contains__(self, item):
        if item in self.broken_files:
            return False
        return item in self.zf.namelist()

    def info(self, name):
        """Get info on a single file."""
        return self.package_contents()[name]

    def package_contents(self):
        """Return a dictionary of file information."""

        if self.contents_cache and not self.broken_files:
            return self.contents_cache

        # Get a list of ZipInfo objects.
        files = self.zf.infolist()
        out_files = {}

        # Iterate through each file in the ZIP.
        for file_ in files:
            if file_.filename in self.broken_files:
                continue

            file_doc = {"name": file_.filename,
                        "size": file_.file_size,
                        "name_lower": file_.filename.lower()}

            file_doc["extension"] = file_doc["name_lower"].split(".")[-1]

            out_files[file_.filename] = file_doc

        self.contents_cache = out_files
        return out_files

    def read(self, filename):
        "Reads a file from the archive and returns a string."

        if filename in self.file_cache:
            return self.file_cache[filename]

        try:
            output = self.zf.read(filename)
        except zlib.error:
            self.broken_files.add(filename)
            raise
        else:
            self.file_cache[filename] = output
            return output

    def write(self, name, data):
        """Write a blob of data to the ZIP manager."""
        self.zf.writestr(name, to_utf8(data))

    def write_file(self, name, path=None):
        """Write the contents of a file from the disk to the ZIP."""

        if path is None:
            path = name

        self.zf.write(path, name)
