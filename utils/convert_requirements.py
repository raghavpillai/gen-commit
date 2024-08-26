import requests


def generate_resource_blocks(requirements_file="requirements.txt"):
    pypi_base_url = "https://pypi.org/pypi"

    resource_blocks = ""

    with open(requirements_file, "r") as file:
        for line in file:
            line = line.strip()

            if line.startswith("-e") or line.startswith("#") or line == "":
                continue

            try:
                pkg_name, version = line.split("==")
            except ValueError:
                print(f"Skipping invalid line: {line}")
                continue

            pkg_info_url = f"{pypi_base_url}/{pkg_name}/{version}/json"
            response = requests.get(pkg_info_url)

            if response.status_code != 200:
                print(f"Failed to fetch package info for {pkg_name}=={version}")
                continue

            pkg_info = response.json()
            # Select the tar.gz distribution URL
            selected_url = next(
                (
                    url_info
                    for url_info in pkg_info["urls"]
                    if url_info["url"].endswith(".tar.gz")
                ),
                None,
            )

            if not selected_url:
                print(f"No .tar.gz distribution found for {pkg_name}=={version}")
                continue

            download_url = selected_url["url"]
            sha256 = selected_url["digests"]["sha256"]

            resource_block = (
                f'resource "{pkg_name}" do\n'
                f'  url "{download_url}"\n'
                f'  sha256 "{sha256}"\n'
                "end\n\n"
            )

            resource_blocks += resource_block

    return resource_blocks


if __name__ == "__main__":
    resources_text = generate_resource_blocks()
    print(resources_text)
