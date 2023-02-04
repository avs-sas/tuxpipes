SUMMARY = "tuxpipes is a tool to run and store gstreamer pipelines."
DESCRIPTION = "A python tool to store and run gstreamer pipelines."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

TUXPIPES_GIT_PROTOCOL ?= "ssh"
TUXPIPES_GIT_BRANCH ?= "master"

SRC_URI = "git://git@github.com/avmihi/TuxPipes.git;branch=master;protocol=ssh;"
SRCREV = "${AUTOREV}"i

RDEPENDS:tuxpipes = " python3"

S = "${WORKDIR}/git"

do_install:append() {
    install -d ${D}/usr/bin
    install -m 0644 ${S}/tuxpipes.py ${D}/usr/bin/tuxpipes
    install -d ${D}/etc/tuxpipes
    install ${S}/pipes.json ${D}/etc/tuxpipes/pipes.json
    install ${S}/pipes.json ${D}/etc/tuxpipes/settings.json
}

FILES_${PN} += "/usr/bin/tuxpipes"

