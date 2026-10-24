// Flip RELEASE_READY to true once the first public release is on GitHub.
// Then the download buttons and the nav go to /download, which reads the
// latest release at build time instead of sample data.
export const RELEASE_READY = false;

export const REPO_URL = "https://github.com/notkainoa/rac";
export const RELEASES_URL = `${REPO_URL}/releases/latest`;
export const LICENSE_URL = `${REPO_URL}/blob/main/LICENSE`;
export const HELIUM_URL = "https://github.com/imputnet/helium";
export const UNGOOGLED_URL = "https://github.com/ungoogled-software/ungoogled-chromium";
