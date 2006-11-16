# Copyright 2006 by Dirk Meyer
# Distributed under the terms of the GNU General Public License v2
#
# Since this module is not released yet, this ebuild only
# installs the dependencies and not the module itself.

# inherit eutils distutils

DESCRIPTION="Kaa Metadata"
HOMEPAGE="http://www.freevo.org/kaa"
SRC_URI=""

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~ia64 ~ppc ~sparc x86"
IUSE="dvd"

DEPEND="${DEPEND}
	dev-python/kaa-base
	dev-libs/libxml2
        dvd? ( >=media-libs/libdvdread-0.9.3 )"
	