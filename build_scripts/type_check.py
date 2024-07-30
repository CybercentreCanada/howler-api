import os
import shlex
import subprocess
import sys
import textwrap


def prep_command(cmd: str):
    print(">", cmd)
    return shlex.split(cmd)


def main():
    print("Removing existing coverage files")
    result = subprocess.check_output(prep_command('find howler -type f -name "*.py"')).decode().strip().split("\n")

    mypy = subprocess.Popen(
        prep_command(f'python -m mypy {" ".join(result)}'),
        stdout=subprocess.PIPE,
    )

    output = ""
    while mypy.poll() is None:
        if mypy.stdout:
            out = mypy.stdout.read(1).decode()
            output += out
            sys.stdout.write(out)
            sys.stdout.flush()

    if mypy.stdout:
        out = mypy.stdout.read().decode()
        output += out
        sys.stdout.write(out)
        sys.stdout.flush()

    return_code = mypy.poll()
    if return_code is not None and return_code > 0:
        if output and os.environ.get("TF_BUILD", ""):

            markdown_output = textwrap.dedent(
                """
            ![Static Badge](https://img.shields.io/badge/type_check-failing-red)

            ```
            """
            ).strip()

            markdown_output += "\n".join(f"    {line}" for line in output.strip().splitlines())

            markdown_output += "\n```"

            print("##vso[task.setvariable variable=error_result]" + markdown_output.replace("\n", "%0D%0A") + "\n\n")

        raise subprocess.CalledProcessError(return_code, mypy.args, output=output, stderr=None)


if __name__ == "__main__":
    main()
