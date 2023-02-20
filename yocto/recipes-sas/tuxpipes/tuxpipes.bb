SUMMARY = "tuxpipes is a tool to run and store gstreamer pipelines."
DESCRIPTION = "A python tool to store and run gstreamer pipelines."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

#TUXPIPES_GIT_PROTOCOL ?= "https"
#TUXPIPES_GIT_BRANCH ?= "main"

SRC_URI = "git://github.com/avs-sas/tuxpipes.git;branch=main;protocol=https;"
SRCREV = "${AUTOREV}"
PV = "1.0+git${SRCPV}"

#RDEPENDS:tuxpipes = " python3"

S = "${WORKDIR}/git"

do_install:append() {
    install -d ${D}/usr/bin
    install -m 0755 ${S}/tuxpipes.py ${D}/usr/bin/tuxpipes
    install -d ${D}/usr/share/tuxpipes
    install -m 0644 ${S}/pipes.json ${D}/usr/share/tuxpipes/pipes.json
    install -m 0644 ${S}/pipes.json ${D}/usr/share/tuxpipes/settings.json
}

FILES_${PN} += "/usr/bin"
FILES_${PN} += "/usr/share/tuxpipes"
