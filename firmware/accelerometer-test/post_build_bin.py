import shutil
import subprocess
from pathlib import Path

Import("env")


def copy_zephyr_bin(source, target, env):
    build_dir = Path(env.subst("$BUILD_DIR"))
    elf_file = build_dir / "firmware.elf"
    zephyr_dir = build_dir / "zephyr"
    zephyr_bin = zephyr_dir / "zephyr.bin"

    objcopy = shutil.which(env.subst("$OBJCOPY"))
    if not objcopy:
        objcopy = env.WhereIs(env.subst("$OBJCOPY"))
    if not objcopy:
        raise RuntimeError("ARM objcopy executable was not found")

    zephyr_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            objcopy,
            "--gap-fill",
            "0xFF",
            "--output-target=binary",
            "--remove-section=.comment",
            "--remove-section=COMMON",
            str(elf_file),
            str(zephyr_bin),
        ],
        check=True,
    )

    if not zephyr_bin.is_file():
        raise RuntimeError("Zephyr BIN artifact was not generated: {}".format(zephyr_bin))


env.AddPostAction("$BUILD_DIR/${PROGNAME}.hex", copy_zephyr_bin)
