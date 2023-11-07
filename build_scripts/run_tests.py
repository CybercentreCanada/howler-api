from pathlib import Path
import shlex
import subprocess
import sys
import time


def prep_command(cmd: str):
    print(">", cmd)
    return shlex.split(cmd)


try:
    print("Removing existing coverage files")
    subprocess.check_call(
        shlex.split("coverage erase --data-file=.coverage"),
    )

    print("Running howler server (with coverage)")
    background_server = subprocess.Popen(
        prep_command("coverage run -m flask --app howler.app run --no-reload"),
    )

    print("Running pytest")
    time.sleep(2)
    pytest = subprocess.check_call(
        prep_command(
            f"pytest --cov=howler --cov-branch --cov-config=.coveragerc.pytest -rsx -vv {sys.argv[1] if len(sys.argv) > 1 else 'test'}"
        ),
    )

    print("Shutting down background server")
    background_server.send_signal(2)
    background_server.wait()

    print("Coverage server is down, combining coverage files")

    workdir = Path(__file__).parent.parent
    if not (workdir / ".coverage.server").exists():
        print("WARN: .coverage.server file missing!")

    if not (workdir / ".coverage.pytest").exists():
        print("WARN: .coverage.pytest file missing!")

    subprocess.check_call(
        prep_command(
            "coverage combine --data-file=.coverage .coverage.server .coverage.pytest"
        ),
    )

except subprocess.CalledProcessError as e:
    print("Error occurred while running script:", e)
    print("Shutting down background server")
    background_server.send_signal(2)
    background_server.wait()
    sys.exit(e.returncode)
