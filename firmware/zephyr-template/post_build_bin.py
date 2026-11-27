import os
import shutil
import subprocess
from pathlib import Path

Import("env")


def find_ninja(env):
    ninja = shutil.which("ninja")
    if ninja:
        return ninja

    ninja = env.WhereIs("ninja")
    if ninja:
        return ninja

    roots = [
        env.subst("$PIOHOME_DIR"),
        os.environ.get("PLATFORMIO_CORE_DIR"),
        str(Path.home() / ".platformio"),
    ]
    names = ("ninja.exe", "ninja")
    for root in roots:
        if not root:
            continue
        package_dir = Path(root)
        if package_dir.name != "packages":
            package_dir /= "packages"
        package_dir /= "tool-ninja"
        for name in names:
            candidates = list(package_dir.rglob(name))
            if candidates:
                return str(candidates[0])

    return None


def copy_zephyr_bin(source, target, env):
    build_dir = Path(env.subst("$BUILD_DIR"))
    zephyr_bin = build_dir / "zephyr" / "zephyr.bin"

    ninja = find_ninja(env)
    if not ninja:
        raise RuntimeError("Ninja executable was not found")

    subprocess.run(
        [ninja, "-C", str(build_dir), "zephyr/zephyr.bin"],
        check=True,
    )

    if not zephyr_bin.is_file():
        raise RuntimeError("Zephyr BIN artifact was not generated: {}".format(zephyr_bin))


env.AddPostAction("$BUILD_DIR/${PROGNAME}.hex", copy_zephyr_bin)
