SUMMARY = "tuxpipes is a tool to run and store gstreamer pipelines."
DESCRIPTION = "A python tool to store and run gstreamer pipelines."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

#TUXPIPES_GIT_PROTOCOL ?= "https"
#TUXPIPES_GIT_BRANCH ?= "main"

SRC_URI = "git://github.com/Software-and-Services/tuxpipes.git;branch=main;protocol=https;"
SRCREV = "${AUTOREV}"
PV = "1.0+git${SRCPV}"

#RDEPENDS:tuxpipes = " python3"

S = "${WORKDIR}/git"

do_install:append() {
    install -d ${D}/usr/bin
    install -m 0644 ${S}/tuxpipes.py ${D}/usr/bin/tuxpipes
    install -d ${D}/etc/tuxpipes
    install -m 0644 ${S}/pipes.json ${D}/etc/tuxpipes/pipes.json
    install -m 0644 ${S}/pipes.json ${D}/etc/tuxpipes/settings.json
}

FILES_${PN} += "/usr/bin/tuxpipes"
FILES_${PN} += "/etc/tuxpipes/pipes.json"
FILES_${PN} += "/etc/tuxpipes/settings.json"
