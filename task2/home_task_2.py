from functools import total_ordering
from itertools import groupby


@total_ordering
class Version:

    def __init__(self, version: str):
        self.version, self.prerelease = self.parse_values(version)

    def __lt__(self, other):
        if self.version < other.version:
            return True
        elif other.version < self.version:
            return False
        elif len(self.prerelease) == 0 and len(other.prerelease) != 0:
            return False
        elif len(self.prerelease) != 0 and len(other.prerelease) == 0:
            return True
        elif self.prerelease < other.prerelease:
            return True
        elif other.prerelease < self.prerelease:
            return False

    def __eq__(self, other):
        if self.version == other.version and self.prerelease == other.prerelease:
            return True
        else:
            return False

    def parse_values(self, version):
        version = version.replace('-', '.').split('.')
        for i in range(3):
            try:
                if version[i].isdigit():
                    version[i] = int(version[i])
                else:
                    string_digit = ["".join(value) for _, value in groupby(version[i], str.isdigit)]
                    for id, item in enumerate(string_digit):
                        if item.isdigit():
                            version[i] = int(item)
            except IndexError:
                return version[:3], version[3:]
        return version[:3], version[3:]


def main():
    to_test = [
        ('1.0.0', '2.0.0'),
        ('1.0.0', '1.42.0'),
        ('1.2.0', '1.2.42'),
        ('1.1.0-alpha', '1.2.0-alpha.1'),
        ('1.0.1b', '1.0.10-alpha.beta'),
        ('1.0.0-rc.1', '1.0.0'),
        ('1.0', '1.1'),
    ]

    for version_1, version_2 in to_test:
        assert Version(version_1) < Version(version_2), 'le failed'
        assert Version(version_2) > Version(version_1), 'ge failed'
        assert Version(version_2) != Version(version_1), 'neq failed'


if __name__ == "__main__":
    main()
