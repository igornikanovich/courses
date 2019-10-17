import re


class Version:

    SemVerRE = re.compile(
        r"""
        ^(?P<major>(0|[1-9]\d*))\.
        (?P<minor>(0|[1-9]\d*))\.
        (?P<patch>(0|[1-9]\d*))
        (?:-(?P<prerelease>
            (?:0|[0-9A-Za-z-][0-9A-Za-z-]*)
            (?:\.(?:0|[0-9A-Za-z-][0-9A-Za-z-]*))*
        ))?
        (?:\+(?P<buildmetadata>[0-9A-Za-z-]+(?:\.[0-9A-Za-z]+)*))?
        """, re.VERBOSE)

    def __init__(self, version):
        MatchRE = self.SemVerRE.match(version)
        self.major = int(MatchRE.group('major'))
        self.minor = int(MatchRE.group('minor'))
        self.patch = int(MatchRE.group('patch'))
        self.prerelease = MatchRE.group('prerelease')
        self.buildmetadata = MatchRE.group('buildmetadata')

    def __lt__(self, other):
        if self.major < other.major:
            return True
        elif other.major < self.major:
            return False
        elif self.minor < other.minor:
            return True
        elif other.minor < self.minor:
            return False
        elif self.patch < other.patch:
            return True
        elif other.patch < self.patch:
            return False
        elif self.prerelease is None and other.prerelease is not None:
            return False
        elif self.prerelease is not None and other.prerelease is None:
            return True
        elif self.prerelease < other.prerelease:
            return True
        elif other.prerelease < self.prerelease:
            return False
        else:
            return False

    def __eq__(self, other):
        if self.major == other.major \
                and self.minor == other.minor \
                and self.patch == other.patch \
                and self.prerelease == other.prerelease:
            return True
        else:
            return False


def main():
    to_test = [
        ('1.0.0', '2.0.0'),
        ('1.0.0', '1.42.0'),
        ('1.2.0', '1.2.42'),
        ('1.1.0-alpha', '1.2.0-alpha.1'),
        ('1.0.1b', '1.0.10-alpha.beta'),
        ('1.0.0-rc.1', '1.0.0'),
    ]

    for version_1, version_2 in to_test:
        assert Version(version_1) < Version(version_2), 'le failed'
        assert Version(version_2) > Version(version_1), 'ge failed'
        assert Version(version_2) != Version(version_1), 'neq failed'


if __name__ == "__main__":
    main()

print(Version('1.0.1b') > Version('1.0.10-alpha.beta'))
print(Version('0.3.0b') < Version('1.2.42'))
print(Version('1.0.0-rc.1') < Version('1.0.0'))
